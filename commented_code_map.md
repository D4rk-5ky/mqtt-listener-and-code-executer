# Commented code map

This map explains the current project, including why each operation exists and its limitations. The listener supports complete payload names and shell commands, including spaces, an optional online announcement, and optional Home Assistant device/button discovery. The unit uses `/root/Source/mqtt-listener-and-code-executer` for its working directory, listener, and config. Shell scripts, the supplied `.gitignore`, and dependency pins are preserved. The build recipe includes the version resource.

## `mqtt-listener.py`

### Imports and entry point

- `#!/usr/bin/env python3` selects Python 3 through the environment when directly executed. The release records mode `0755` so direct execution works after Unix-aware extraction. Activate the environment containing Paho before direct launch, or select its interpreter explicitly; the service selects an interpreter explicitly.
- `paho.mqtt.client as mqtt` supplies the MQTT client. Import occurs before argument parsing, so even help requires the dependency.
- `subprocess` supplies process creation. `argparse` supplies CLI parsing and usage errors.
- `hashlib.sha256` produces stable discovery IDs from full command names; `json.dumps` serializes discovery safely without exposing shell commands; `re.fullmatch` restricts device IDs to HA discovery path characters.
- `Path` locates `VERSION` beside `__file__`, independently of the working directory. `resolve().with_name(...)` selects the sibling path; `read_text(encoding='utf-8').strip()` reads the release number once. This single source also works with the version resource included by the build spec. A missing/unreadable version file stops startup instead of reporting an invented version.
- `if __name__ == '__main__'` starts the application only on direct execution, allowing functions to be imported for testing.

### `read_config(file_path)`

Opens the supplied text file in read mode using Python's default text encoding. It builds a settings dictionary and a command dictionary while tracking the current section.

1. `strip()` trims each line; empty lines and whole-line `#` comments are skipped for readable config files.
2. Within `commands`, a line containing `=` is split once into trimmed payload and shell command, then processing continues with the next line. Internal spaces, quotes, shell operators, later equals signs, and a trailing colon remain intact. Mapping detection comes first so command text ending in `:` cannot accidentally change sections or discard following mappings. No tokenization or whitespace normalization is applied inside either field.
3. Otherwise, a line ending in `:` changes the section. `commands:` attaches the shared command dictionary to `config['commands']`; other section headers only change the section marker. An empty setting such as `password:` is still treated as a section header, not a stored empty value. Omit unused credential lines instead.
4. Otherwise, a line containing `:` is split once into a setting. Values are stored as strings. Later duplicate keys overwrite earlier ones.
5. Returns the dictionary. There is no schema validation, inline comment removal, YAML parsing, interpolation, or exception handling for file access.

### `get_online_topic(config, topics)`

Reads and strips the optional `online_topic`. Missing/blank values return `None`, keeping legacy configs unchanged. The shared `valid_publish_topic()` validator rejects wildcards (`+`, `#`), null characters, and UTF-8 length above MQTT's 65535-byte limit. These invalid values, or an exact match to an existing command topic log a warning and return `None`. This disables only announcing, without taking an existing command topic out of service. A valid distinct topic is returned and reserved for status. Wildcard command subscriptions may match it; the incoming callback ignores that exact topic. No broker settings, command strings, or subscription filters are rewritten.

### `on_connect(client, userdata, flags, rc)`

Paho's legacy four-argument connection callback prints the result code. For every entry in `userdata['topics']`, it calls `client.subscribe(topic)` and logs the topic. This preserves subscription requests after connection/reconnection using the library's default QoS (0). `flags` is unused. The original subscription loop does not gate on `rc` or inspect subscription return values; its log is not broker acknowledgment.

After that loop, `rc == 0` and a configured status topic allow `client.publish(online_topic, payload='online', qos=1, retain=False)`. This uses the same authenticated connection, sends a plain payload after successful CONNACK, and also runs on reconnect. It does not wait for SUBACK or prove command readiness. The return object's `rc` is compared with `mqtt.MQTT_ERR_SUCCESS`: a successful queue operation or an error is logged. A try/except prevents publication errors from escaping the callback. No `wait_for_publish()` is used because blocking this callback would prevent the same network loop from processing acknowledgments. QoS 1 permits redelivery. This original announcement has no Last Will or heartbeat. Optional HA discovery uses a separate availability Last Will.

On successful connections with HA enabled, `on_connect` also subscribes to the HA birth topic at QoS 1 and calls `publish_home_assistant_discovery` immediately. That initial publication means a retained broker replay of the HA `online` birth payload is redundant and is filtered later in `on_message`. Birth subscription failures are logged without preventing discovery or existing command handling. Failed connections do not announce HA discovery.

### `on_message(client, userdata, msg)`

First returns without decoding or launching anything when `msg.topic` equals the configured status topic. MQTT 3 supplies no publisher identity, so reserving that topic prevents a wildcard subscription from executing a returned self-announcement; messages from other publishers on the reserved topic are ignored too. The same `online` payload remains eligible as a command on original command topics.

When HA is enabled, the birth topic is checked next. All birth-topic messages return without command handling. Rediscovery happens only when the payload exactly matches the configured birth bytes **and** `msg.retain` is false. A retained broker replay is ignored because `on_connect` has already published the complete discovery snapshot for that connection. `getattr(msg, 'retain', False)` keeps synthetic/legacy message objects without a retain attribute compatible while real Paho messages provide it. The HA availability topic and the device discovery namespace also return before decoding, so wildcard subscriptions cannot turn metadata into commands.

For all other topics, calls `msg.payload.decode().strip()` to decode UTF-8 and remove surrounding whitespace, then logs the payload and topic. Invalid UTF-8 is outside the process-launch try/except and can raise from the callback, as before.

Looks up the whole exact, case-sensitive payload, including internal spaces, in `userdata['commands']`. An unknown or empty mapping logs “No command found” and returns without launching a process. The incoming payload is not interpolated into the configured shell text.

For a nonempty mapping, `subprocess.Popen(command, shell=True)` starts the configured text through the operating system shell without waiting. This keeps callbacks from blocking on job completion. The try/except logs process-creation errors, but cannot determine later command success. There is no child process tracking, timeout, result publication, duplicate suppression, retained **command-message** filter, or topic-specific command map. The only retained-message suppression is the reserved HA birth/status replay described above.

### `valid_publish_topic(topic)`

Returns true only for a nonempty topic with no `+`, `#` or null character and at most 65535 UTF-8 bytes. Both the original online-topic validator and the HA validator reuse this function, keeping their common rules in one place.

### `get_home_assistant_config(config, topics, online_topic)`

Returns `None` immediately when `ha_enabled` is omitted or false, preserving legacy behavior. When true, validates the stable ASCII device ID, nonempty name, strict boolean retain setting, nonempty birth payload, and concrete publish topics. It reserves room for the generated hash/config suffix when checking the full discovery topic length. `mqtt.topic_matches_sub` reuses Paho's MQTT matcher to ensure the HA command topic is already covered by a command subscription; it does not add a second command subscription.

The function rejects exact command/status conflicts, shared birth/availability/original-online topics, and command/status paths inside this device's discovery namespace. Broad subscriptions remain allowed because `on_message` reserves the metadata paths before command dispatch. A validation error is logged and returns `None`, disabling only HA integration. Valid settings are normalized into a dictionary stored in `userdata['home_assistant']` for callbacks. Defaults and all nine HA settings are listed in README and the config example.

### `publish_home_assistant_message(client, topic, payload, retain)`

Queues one discovery or availability message at QoS 1. It checks the Paho return code and catches publication exceptions so a failed metadata publish does not stop the next button or existing command handling. It never waits for PUBACK inside the network callback. Successful queuing is not proof that HA received the message.

### `publish_home_assistant_discovery(client, userdata)`

Returns when HA is disabled. Builds one shared device block with a project-specific stable identifier, configurable name, model, manufacturer, and current `VERSION`. For each nonempty command name and nonempty shell mapping, hashes the exact UTF-8 name with SHA-256 for a stable path-safe ID. The name and `payload_press` remain the original trimmed command name, preserving Unicode, punctuation, and internal spaces. Only the left-hand name is advertised; no shell command is sent to HA.

Publishes one JSON button definition to `<discovery_base>/<hash>/config` with the chosen retain setting, shared device block, availability topic, and existing command topic. Button presses are configured as QoS 0 and non-retained. After definitions, publishes retained `online` availability. Connect/reconnect and fresh non-retained exact HA birth messages reuse this function; retained birth replays do not. Removed discovery topics are not automatically cleared: README explains retained-topic cleanup.

### Main-block operations

| Operation | Purpose and behavior |
| --- | --- |
| `ArgumentParser(description=...)` | Creates usage/help and default `-h`/`--help`; help exits successfully. Its epilog explains exact matching, background shell execution, and retained/repeated messages. |
| `add_argument('-c', '--config', required=True, ...)` | Requires one config path for listening and explains relative paths and the absence of a default. |
| `add_argument('--version', action='version', ...)` | Prints the program name and `VERSION`, then exits 0 before required-config validation, config access, or client creation. Help describes this behavior. |
| `parse_args()` | Parses the CLI; missing/unknown arguments terminate with argparse errors. |
| `read_config(args.config)` | Uses the existing parser rather than duplicating it. Relative paths use the working directory. |
| `config.get('hostname', 'localhost')` | Selects broker host with localhost fallback. |
| `int(config.get('port', 1883))` | Selects numeric port; invalid text raises before connecting. |
| `config.get('username')`, `config.get('password')` | Reads optional authentication strings. |
| Topic list comprehension | Splits `topics` on commas and trims each filter; missing topics yields `['']`, not a valid default subscription. |
| `config.get('commands', {})` | Supplies an empty mapping if no command section exists. |
| `userdata = ...` / `get_online_topic(config, topics)` | Preserves the original topics/commands dictionary, adding only a valid nonempty `online_topic`. |
| `get_home_assistant_config(config, topics, online_topic)` | Validates opt-in discovery and adds its settings to userdata only when enabled and valid. |
| `mqtt.Client(userdata=userdata)` | Creates the same client with settings shared with callbacks; remaining options use Paho defaults. The dependency is pinned to retain the legacy callback API. |
| `client.on_connect = ...`, `client.on_message = ...` | Registers the two existing callbacks. |
| `client.will_set(...)` | With valid HA settings only, registers retained `offline` at QoS 1 on the separate availability topic before connecting. Broker-detected disconnect makes buttons unavailable. |
| `if username and password` / `username_pw_set` | Enables authentication only when both strings are nonempty. |
| `client.connect(hostname, port, 60)` | Starts the broker connection with 60-second keepalive. There is no TLS setup. |
| `client.loop_forever()` | Runs Paho's network loop and callback dispatch. Transport/reconnection details depend on the installed Paho version. |

## Configuration and ignore files

`commands-example.txt` lists all seven existing listener settings/sections, nine optional HA settings after the MQTT settings, and four power-command mappings. HA is disabled by default; the device name and stable ID are editable. Its whole-line comments explain defaults, authentication, topics, status, and paths. Each mapping starts with one literal tab; the parser's `strip()` accepts tabs or spaces. Commented optional examples explain complete Docker payloads, short aliases, quoted paths/arguments, and commands ending in a colon. The four active power payload names and all broker values are preserved; helper paths point to `/root/Source/mqtt-listener-and-code-executer/scripts/`. Copy it to a private local `commands.txt`, adapt it, and initially test with only a harmless command. The application does not select this filename automatically.

The supplied `.gitignore` contains `commands*` and `! commands-example.txt`. `commands*` ignores matching files; the space after `!` prevents the intended example exception. Its bytes are preserved. The upload does not contain the `.gitigore` mentioned in historical release records.

## Shell helpers: every command/operator

The four helpers are located in the project-root `scripts/` directory. Their content and executable permissions are unchanged. All four scripts begin with `#!/bin/bash` to use Bash.

| Script / expression | What it does and why |
| --- | --- |
| `scripts/shutdown-delay.sh`: `(sleep 60 && shutdown -P now) &` | Starts a subshell in the background. `sleep 60` delays for 60 seconds; `&&` executes the power command only if sleep succeeds. `shutdown -P now` requests immediate power-off after that delay; `-P` selects power-off and `now` selects immediate timing. |
| `scripts/reboot-delay.sh`: `(sleep 60 && reboot) &` | Same background delay, then requests reboot if sleep succeeded. |
| Both delay scripts: `echo $! > /tmp/...pid` | `$!` is the latest background job PID. `echo` writes it; `>` creates or overwrites the shutdown/reboot PID file so a later cancel call can read it. No completion cleanup is registered. |
| Both cancel scripts: `[ -f /tmp/...pid ]` | Tests whether the relevant PID path is a regular file before reading it. |
| `cat /tmp/...pid` inside `$(...)` | Reads that file and substitutes its text as the PID. Double quotes keep the substitution as one shell argument. |
| `kill "$(cat /tmp/...pid)"` | Sends the default termination signal to the recorded PID; it does not validate that this is still the expected job or explicitly target its process group. |
| `&& rm /tmp/...pid` | Removes the record only if the preceding kill succeeds. A failed kill leaves the file. Each `&&` short-circuits later commands on failure. |

The shutdown files use `/tmp/shutdown.pid`; reboot files use `/tmp/reboot.pid`. Repeated delays overwrite their records without cancelling older jobs. PID reuse and stale files are possible. Cancellation reliability and Linux process behavior have not been verified on a live target; these scripts are preserved rather than rewritten.

## `mqtt-listener.service`: every directive and command

| Entry | Purpose / limitation |
| --- | --- |
| `[Unit]` | General metadata and ordering. |
| `Description=MQTT Client Script` | Human-readable description in systemd. |
| `After=network.target` | Orders start after this target when both are scheduled; does not guarantee broker availability. |
| `[Service]` | Process launch and lifecycle settings. |
| `Type=simple` | Treats the launched process as the main service without a readiness protocol. |
| `User=your_username` | Placeholder account; replace it with an account allowed to run the configured commands. |
| `WorkingDirectory=/root/Source/mqtt-listener-and-code-executer/` | Requested project working directory; must exist and be accessible to the selected account. Adapt for your installation. |
| `TimeoutStartSec=180` | Allows up to 180 seconds for service startup, including its pre-start command. |
| `ExecStartPre=/bin/sleep 60` | Delays each start by 60 seconds; it does not actively probe broker readiness. |
| `ExecStart=/usr/bin/python3 -u /root/Source/mqtt-listener-and-code-executer/mqtt-listener.py -c /root/Source/mqtt-listener-and-code-executer/commands.txt` | Starts Python with unbuffered logs (`-u`) and the listener's explicit configuration (`-c`). Change interpreter and paths together for a virtual environment. |
| `Restart=always` | Restarts after process exits according to systemd rules; explicit systemctl stop does not trigger restart. |
| `[Install]` | Settings used when enabling the service. |
| `WantedBy=multi-user.target` | Adds the unit to this normal boot target when enabled. |

The README explains every installation/publisher command and its flags: `cd`, Python `-m venv`/`-m pip`, `cp`, `chmod`, `mosquitto_pub`, `sudo`, `systemctl`, and `journalctl`. Its `/root/Source/mqtt-listener-and-code-executer` paths are an adaptable example; the packaged service uses this project directory for its working directory and both file paths.

## Release and verification files

- `README.md`: current setup, flags, options, helper behavior, and limits; no release history.
- `VERSION`: single release number used by the application `--version` action and bundled executable.
- `VERSIONING.md`: increment/rollover rule and every change for each created version.
- `manifest.sha256`: hashes for every release file except itself. Paths are relative to the release root; changed originals are explicitly described in the version record and verification notes.
- `VERIFICATION.md`: performed checks, preservation results, and untested deployment areas.
- `tests/test_listener.py`: reusable offline tests; never connects to MQTT or executes configured commands.
- `tests/test_online.py`: offline announcement, compatibility, and self-message isolation tests.
- `tests/test_home_assistant.py`: discovery, identity, config validation, metadata isolation, button dispatch, and Last Will wiring tests.
- `uploaded-release-manifest.json`: exact provenance for the uploaded 0.0.8 baseline used to create 0.0.9. It records all 20 supplied files, relative paths, sizes, SHA-256 hashes, raw ZIP Unix-mode fields, the source ZIP hash, and the two names referenced by the uploaded checksum manifest but absent from that ZIP. It is descriptive input evidence, not a replacement for the current `manifest.sha256`. A zero mode means the input ZIP entry supplied no Unix permission bits.
- `requirements.txt`: pins Paho 2.1.0, which supports the existing legacy four-argument connection callback. Paho may issue a deprecation warning for that callback API; it is deliberately preserved for this focused change.
- `requirements-build.txt`: includes runtime requirements with `-r requirements.txt` and pins PyInstaller 6.22.3. It is used only in the build environment.
- `mqtt-listener.spec`: standalone executable build definition, explained below.

## Test functions and commands

`fake_paho()` creates a synthetic Paho module tree and mocked client so tests do not need the dependency or a broker. Its topic matcher conservatively matches exact topics; the HA wildcard-wiring test patches that method explicitly, and the release broker test exercises the real Paho matcher. `load_listener()` executes the script under a non-main name with these modules installed temporarily, exposing its functions without starting it. `ListenerTests.setUp()` loads a fresh namespace for each case. `parse()` supplies in-memory config through mocked file access. `run_cli()` temporarily supplies argv, config text, and fake MQTT, then executes the real main block under captured stdout/stderr. It returns the mocked client and output for startup assertions; SystemExit is allowed through for CLI error tests. `message()` invokes the real callback with captured logs and mocked `Popen`, returning the mock for execution assertions.

Each `test_*` method names a distinct contract: parser defaults/splitting/duplicates, example options, matching/unknown payloads, retained/repeated delivery, launch exceptions, invalid decoding, subscription requests, main startup/authentication, help, or CLI/config errors. The test module's `unittest.main()` guard supports direct execution. The README's `python3 -B -m unittest discover -s tests -v` runs them with no bytecode output. Compilation for release verification uses Python's built-in `compile()` in memory; no compiled files are distributed.

| Test method | Contract and reason |
| --- | --- |
| `test_config_comments_trimming_and_first_equals` | Checks readable config formatting and preservation of equals signs in commands. |
| `test_multiword_mapping_reaches_callback_as_complete_command` | Parses the requested Docker example with no indentation, spaces, or tabs and verifies one complete configured command reaches Popen. |
| `test_multiword_payload_requires_exact_internal_text` | Rejects partial, case-changed, spacing-changed, quoted, and appended payloads to preserve the configured-command boundary. |
| `test_command_ending_in_colon_preserves_mapping_and_following_commands` | Prevents section-header detection from swallowing a valid shell command or subsequent Docker mapping. |
| `test_quoted_arguments_equals_and_internal_spaces_are_preserved` | Checks complete shell text survives parsing and dispatch with quoted paths, arguments, repeated spaces, equals signs, and a URL. |
| `test_main_and_callback_keep_multiword_mapping_and_status_isolation` | Passes a multiword mapping through real main-block wiring; ignores it on the reserved status topic and launches it exactly once on the command topic. |
| `test_config_duplicates_use_last_value` | Records overwrite behavior for duplicate settings/mappings. |
| `test_config_empty_value_is_section_and_inline_comments_remain` | Records parser edge cases so docs do not imply YAML semantics. |
| `test_example_has_every_setting_and_original_payload` | Ensures every supported option and original payload is represented, with existing helpers under `scripts/` and the configured deployment prefix. |
| `test_message_trims_and_launches_only_configured_command` | Confirms exact mapped shell text is passed to mocked Popen after trimming. |
| `test_unknown_case_mismatch_and_shell_payload_do_not_launch` | Ensures unknown text, wrong case, and shell-like incoming text cannot bypass the mapping. |
| `test_empty_command_does_not_launch` | Records the nonempty-command condition. |
| `test_retained_and_repeated_messages_are_not_filtered` | Confirms there is no retained-message or duplicate suppression. |
| `test_launch_error_is_logged_without_escaping_callback` | Checks that process-creation errors are caught and logged. |
| `test_invalid_utf8_raises_before_launch` | Records the unhandled decoding error without running any commands. |
| `test_connect_requests_each_topic_even_on_failure_code` | Records subscription attempts and absence of result-code gating. |
| `test_main_passes_config_to_client_and_registers_callbacks` | Checks actual main-block wiring, auth, port, keepalive, callbacks, and network-loop request using fake MQTT. |
| `test_main_defaults_and_incomplete_credentials_skip_auth` | Checks fallback settings and the requirement for both credentials. |
| `test_help_exits_zero_and_lists_flags_without_creating_client` | Runs both help aliases through the real parser using a fake dependency; permits argparse alias formatting differences while checking the documented flags. |
| `test_missing_config_unknown_flag_and_missing_value_exit_two` | Checks argparse errors for missing config, missing values, and the unsupported dry-run flag. |
| `test_version_exits_zero_without_config_or_client` | Checks version output against the shared VERSION file, successful exit without required config, and no config read or MQTT client creation. |
| `test_invalid_port_raises` | Records unhandled non-integer configuration. |
| `test_missing_config_file_raises` | Records unhandled file-read failure. |

## Online tests: every method

`OnlineTests.setUp()` loads fresh functions and sets up a fake MQTT client, a wildcard command subscription, a status topic, and an `online` command mapping. `connect(rc=0)` runs the real connection callback with captured output so tests can inspect logs without networking. Tests reuse `load_listener()` and `ListenerTests.run_cli()`/`parse()` instead of creating duplicate loaders/parsers.

| Test method | Contract and reason |
| --- | --- |
| `test_online_on_successful_connect_and_reconnect` | Verifies identical plain payload/QoS/non-retained publishing after two successful callbacks, original subscription requests, and no blocking wait for publish. |
| `test_refused_connection_does_not_announce` | Ensures a rejected connection cannot claim online. |
| `test_missing_online_topic_preserves_legacy_behavior` | Verifies old configs keep their subscriptions without publishing. |
| `test_announcement_errors_do_not_stop_callback` | Verifies exceptions in publishing are logged and contained. |
| `test_publish_error_result_is_logged` | Checks the non-exception publication error-code path. |
| `test_status_topic_is_ignored_before_decoding_or_command_lookup` | Proves self-echo cannot launch an identically named command; even malformed payload bytes on the reserved topic are ignored. |
| `test_online_remains_a_command_on_original_command_topics` | Proves payload names are not globally blocked by the new feature. |
| `test_validation_disables_invalid_and_exact_conflicting_topics` | Rejects invalid publish topics and exact command-topic collisions without altering command settings. |
| `test_missing_or_blank_topic_disables_feature` | Checks safe opt-in behavior for legacy configs. |
| `test_valid_topic_with_wildcard_subscription_is_reserved` | Allows an independent status topic even if a broad subscription receives it. |
| `test_main_adds_only_valid_online_topic_to_userdata` | Checks real startup wiring with the new config option and tabbed command mapping. |
| `test_tabs_and_spaces_parse_identically` | Confirms the requested tab indentation uses the existing parser unchanged. |

## Home Assistant tests: every helper and method

These tests reuse `test_listener` loaders and main-block helpers. All process launches are mocked.

| Function/method | Purpose |
| --- | --- |
| `setUp` | Loads existing test helpers, default HA settings, fake MQTT capture, output capture, and a mocked process launcher. Cleanup restores each patch. |
| `settings` | Calls the real config validator with optional settings/topics overrides, avoiding a second implementation. |
| `discover` | Calls the real discovery publisher and returns decoded captured button definitions. |
| `buttons` | Decodes only captured config-topic messages so tests inspect actual discovery JSON. |
| `message` | Passes a synthetic MQTT message through the existing on_message callback with optional retention. |
| `test_each_command_has_exact_label_payload_and_shared_device` | Checks all names, payloads, device grouping/version, discovery paths, availability and retain/QoS settings; shell text is not disclosed. |
| `test_button_press_reuses_exact_existing_command_dispatch` | Feeds discovered press payloads back to the real handler and checks the configured shell command reaches mocked Popen. |
| `test_ids_stable_across_order_command_and_device_name_changes` | Ensures harmless configuration edits update existing entities without identity changes. |
| `test_similar_names_and_different_devices_have_distinct_ids` | Prevents punctuation, casing, Unicode, spacing and listener identity collisions. |
| `test_empty_names_or_commands_are_not_advertised` | Avoids buttons for mappings that cannot usefully run. |
| `test_disabled_and_legacy_configs_add_no_client_behavior` | Confirms opt-out adds no Will, publication, or birth subscription. |
| `test_invalid_settings_disable_only_discovery` | Rejects malformed IDs, flags, topics and conflicts while preserving ordinary command startup. |
| `test_online_topic_and_discovery_namespace_collisions_are_rejected` | Ensures HA metadata cannot replace original status or explicit command paths. |
| `test_custom_settings_and_wildcard_with_explicit_command_topic` | Checks configurable metadata paths, birth payload and retain behavior; confirms wildcard coverage delegates to Paho. |
| `test_connect_reconnect_and_refused_connection` | Checks rediscovery and birth subscriptions after success, and no HA publication after refusal. |
| `test_ha_birth_ignores_retained_replay_and_republishes_fresh_birth` | Regression test for the 0.0.10 fix: a retained HA `online` replay causes no discovery publication or shell dispatch, while a fresh non-retained default/custom birth payload still republishes discovery without executing commands. |
| `test_metadata_is_reserved_before_decoding_with_broad_subscriptions` | Blocks metadata from command execution or UTF-8 decoding, preserving online as a normal command on command topics. |
| `test_announcement_and_discovery_coexist` | Preserves original non-retained online announcements alongside HA discovery. |
| `test_publish_errors_do_not_stop_remaining_discovery_or_commands` | Exercises exception and error-code handling while later metadata and commands still work. |
| `test_birth_subscription_error_still_publishes_discovery` | Handles subscription exceptions and error return codes independently of discovery. |
| `test_main_configures_last_will_before_connect_and_reuses_callbacks` | Checks main-block Will settings/order and existing callback registration. |
| `test_topic_validation_handles_utf8_byte_limit` | Checks byte length rather than character length and rejects empty/wildcard/null topics. |

## PyInstaller spec: every operation

- `Path(SPECPATH)` resolves the project directory from the spec's location, so its entry-script path is explicit.
- `collect_all('paho.mqtt')` supplies Paho submodules, data, and binaries, including modules imported indirectly. Python standard-library modules referenced by the script are discovered by PyInstaller's analysis.
- `datas.append((str(project / 'VERSION'), '.'))` puts the shared version file at the bundle root beside the entry script so `--version` works in the executable.
- `Analysis([...], pathex=[...], binaries=..., datas=..., hiddenimports=...)` analyzes the existing listener and collected MQTT dependencies. Empty hook/exclusion lists use default hooks and exclude no modules; `noarchive=False` allows Python-module archiving.
- `PYZ(analysis.pure)` builds the bundled Python module archive.
- `EXE(...)` includes that archive, scripts, binaries, and data in one executable. `('u', None, 'OPTION')` enables unbuffered Python stdout/stderr inside the bundle for service logs. The name is `mqtt-listener`; `console=True` preserves normal CLI/log output. `debug=False`, `strip=False`, and `upx=False` disable debug bootloader output, binary stripping, and UPX compression. `bootloader_ignore_signals=False` retains ordinary bootloader signal behavior.
- There is no `COLLECT` stage because this spec produces a one-file executable. Config and referenced helper scripts are not bundled or copied: absolute command paths continue to identify the user's external files.
- The README explains `python -m PyInstaller --clean --noconfirm mqtt-listener.spec`, requirements installation, output paths, and the executable's `--help`, `--version`, and `--config` flags. A build must match the target OS/architecture; Windows builds do not substitute for Linux service builds.

## Complete-command and direct-execution usage

- `docker start open-webui` starts the existing Docker container named `open-webui`; it requires Docker access under the listener account. As a left-side payload it is matched as one complete string; as right-side shell text it is launched unchanged. The config examples are commented to avoid enabling it unintentionally.
- `start_webui` is an optional short payload alias for the same Docker command.
- `run tool = "/opt/my tools/runner" --label="A B"` demonstrates shell quoting of an executable path and argument with spaces; the path is a placeholder.
- `print label = printf label:` demonstrates a command ending with a colon. `printf` writes the literal `label:` text in this example.
- `. .venv/bin/activate` loads the environment into the current shell so the script's `env python3` header finds its dependencies. `./mqtt-listener.py --help` runs the local executable and prints usage. `--version` prints the application name and version and exits; `--config` (alias `-c`) selects its config file.
- `chmod +x mqtt-listener.py scripts/shutdown-delay.sh scripts/shutdown-cancel.sh scripts/reboot-delay.sh scripts/reboot-cancel.sh` restores execution permission for all five scripts if extraction dropped it.
- `mosquitto_pub ... -m 'docker start open-webui'` uses shell quotes to pass one complete MQTT payload; the quotes are not transmitted. Host, port, and topic flags are explained in README.
- `sha256sum -c manifest.sha256` checks every listed release-file checksum, excluding the manifest itself. On macOS, `shasum -a 256 -c manifest.sha256` performs the same check. These validate file contents against the supplied list, not publisher identity.

## HA discovery cleanup command

`mosquitto_pub -h localhost -p 1883 -t <old-config-topic> -r -n` publishes an empty retained discovery definition. `-h` selects the broker, `-p` the port, `-t` the exact obsolete config topic, `-r` retention, and `-n` an empty payload. This removes an obsolete discovered entity and clears its retained definition. It is a manual maintenance command; the listener does not run it. README explains names, hash IDs, device settings, and the Home Assistant setup steps.
