"""Exercise discovery and existing command dispatch without a broker or processes."""
import contextlib
import io
import json
import types
import unittest
from unittest.mock import MagicMock, patch

import test_listener
from test_listener import load_listener


class HomeAssistantTests(unittest.TestCase):
    def setUp(self):
        self.listener = load_listener()
        self.config = {'ha_enabled': 'true', 'ha_device_id': 'test-device',
                       'ha_device_name': 'My Server'}
        self.topics = ['device/commands', 'device/#']
        self.data = {'topics': self.topics, 'commands': {
            'shutdown_delay': '/trusted/power.sh',
            'docker start open-webui': 'docker start open-webui',
            'Backup Æ "photos"': '/trusted/backup.sh'}}
        self.data['home_assistant'] = self.settings()
        self.client = MagicMock()
        self.client.publish.return_value.rc = 0
        self.client.subscribe.return_value = (0, 1)
        self.logs = io.StringIO()
        capture = contextlib.redirect_stdout(self.logs)
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)
        launch = patch.object(self.listener['subprocess'], 'Popen')
        self.launch = launch.start()
        self.addCleanup(launch.stop)

    def settings(self, updates=None, topics=None, online_topic=None):
        config = dict(self.config)
        config.update(updates or {})
        return self.listener['get_home_assistant_config'](
            config, self.topics if topics is None else topics, online_topic)

    def discover(self):
        self.listener['publish_home_assistant_discovery'](self.client, self.data)
        return self.buttons()

    def buttons(self):
        return {call.args[0]: json.loads(call.kwargs['payload'])
                for call in self.client.publish.call_args_list if call.args[0].endswith('/config')}

    def message(self, topic, payload, retained=False):
        self.listener['on_message'](self.client, self.data, types.SimpleNamespace(
            topic=topic, payload=payload, retain=retained))

    def test_each_command_has_exact_label_payload_and_shared_device(self):
        buttons = self.discover()
        self.assertEqual(len(buttons), 3)
        self.assertEqual({b['name'] for b in buttons.values()}, set(self.data['commands']))
        for topic, button in buttons.items():
            self.assertEqual(button['name'], button['payload_press'])
            self.assertEqual(button['device']['name'], 'My Server')
            self.assertEqual(button['device']['identifiers'], ['mqtt_listener_test-device'])
            self.assertEqual(button['device']['sw_version'], self.listener['VERSION'])
            self.assertEqual(button['command_topic'], 'device/commands')
            self.assertEqual(button['availability_topic'], 'mqtt-listener/test-device/availability')
            self.assertFalse(button['retain'])
            self.assertEqual(button['qos'], 0)
            self.assertTrue(topic.startswith('homeassistant/button/mqtt_listener_test-device/'))
        self.assertTrue(all(c.kwargs['retain'] for c in self.client.publish.call_args_list))
        self.launch.assert_not_called()
        self.assertNotIn('/trusted/', str(self.client.publish.call_args_list))

    def test_button_press_reuses_exact_existing_command_dispatch(self):
        for button in self.discover().values():
            self.message(button['command_topic'], button['payload_press'].encode())
            self.launch.assert_called_with(self.data['commands'][button['name']], shell=True)
        self.assertEqual(self.launch.call_count, 3)

    def test_ids_stable_across_order_command_and_device_name_changes(self):
        first = self.discover()
        self.client.reset_mock()
        self.data['commands'] = {name: 'changed executable' for name in reversed(self.data['commands'])}
        self.data['home_assistant']['device_name'] = 'Renamed Server'
        second = self.discover()
        self.assertEqual(set(first), set(second))
        self.assertEqual({b['unique_id'] for b in first.values()}, {b['unique_id'] for b in second.values()})
        self.assertTrue(all(b['device']['name'] == 'Renamed Server' for b in second.values()))

    def test_similar_names_and_different_devices_have_distinct_ids(self):
        self.data['commands'] = {name: 'echo configured' for name in ['a b', 'a_b', 'a-b', 'A b', 'a  b', 'æ']}
        first = self.discover()
        self.assertEqual(len(first), 6)
        ids = {b['unique_id'] for b in first.values()}
        self.assertEqual(len(ids), 6)
        self.client.reset_mock()
        self.data['home_assistant'] = self.settings({'ha_device_id': 'second'})
        self.assertFalse(ids & {b['unique_id'] for b in self.discover().values()})

    def test_empty_names_or_commands_are_not_advertised(self):
        self.data['commands'] = {'': 'echo empty', 'disabled': '', 'ping': 'echo ping'}
        self.assertEqual([b['name'] for b in self.discover().values()], ['ping'])

    def test_disabled_and_legacy_configs_add_no_client_behavior(self):
        for config in ('topics: device/commands\n', 'topics: device/commands\nha_enabled: false\n'):
            constructor, _ = test_listener.ListenerTests().run_cli(['-c', 'x'], config)
            client = constructor.return_value
            data = constructor.call_args.kwargs['userdata']
            self.assertNotIn('home_assistant', data)
            client.will_set.assert_not_called()
            client.on_connect(client, data, {}, 0)
            client.publish.assert_not_called()
            client.subscribe.assert_called_once_with('device/commands')

    def test_invalid_settings_disable_only_discovery(self):
        cases = [{'ha_enabled': 'maybe'}, {'ha_device_id': ''}, {'ha_device_id': 'a/b'},
                 {'ha_device_id': 'x'*129}, {'ha_device_name': ''},
                 {'ha_discovery_prefix': '#'}, {'ha_discovery_prefix': '/'},
                 {'ha_discovery_prefix': 'x'*65535}, {'ha_discovery_retain': 'maybe'},
                 {'ha_command_topic': 'different'}, {'ha_command_topic': 'device/#'},
                 {'ha_availability_topic': 'device/commands'},
                 {'ha_status_topic': 'device/commands'}, {'ha_status_topic': 'bad\x00topic'},
                 {'ha_status_topic': 'homeassistant/+'}, {'ha_status_online_payload': ''},
                 {'ha_availability_topic': 'homeassistant/status'},
                 {'ha_status_topic': 'homeassistant/button/mqtt_listener_test-device/x/config'}]
        for config in cases:
            with self.subTest(config=config):
                self.assertIsNone(self.settings(config))
        constructor, _ = test_listener.ListenerTests().run_cli(['-c', 'x'],
            'topics: device/commands\nha_enabled: true\nha_device_id: invalid/id\ncommands:\nping = echo safe\n')
        client = constructor.return_value
        data = constructor.call_args.kwargs['userdata']
        self.assertEqual(data, {'topics': ['device/commands'], 'commands': {'ping': 'echo safe'}})
        client.will_set.assert_not_called()
        client.connect.assert_called_once()

    def test_online_topic_and_discovery_namespace_collisions_are_rejected(self):
        self.assertIsNone(self.settings(online_topic='homeassistant/status'))
        self.assertIsNone(self.settings(online_topic='mqtt-listener/test-device/availability'))
        self.assertIsNone(self.settings(online_topic='homeassistant/button/mqtt_listener_test-device/x'))
        self.assertIsNone(self.settings(topics=['homeassistant/button/mqtt_listener_test-device/x']))
        self.assertIsNotNone(self.settings(online_topic='device/status'))
        # A wildcard covering both endpoints must not conceal a collision.
        with patch.object(self.listener['mqtt'], 'topic_matches_sub', return_value=True):
            for topic in ('homeassistant/status', 'mqtt-listener/test-device/availability',
                          'homeassistant/button/mqtt_listener_test-device/x/config', 'device/status'):
                self.assertIsNone(self.settings({'ha_command_topic': topic},
                                                topics=['#'], online_topic='device/status'))

    def test_custom_settings_and_wildcard_with_explicit_command_topic(self):
        with patch.object(self.listener['mqtt'], 'topic_matches_sub', return_value=True) as matcher:
            ha = self.settings({'ha_discovery_prefix': 'custom/ha/', 'ha_command_topic': 'device/commands',
                                'ha_availability_topic': 'custom/availability', 'ha_status_topic': 'custom/status',
                                'ha_status_online_payload': 'ready', 'ha_discovery_retain': 'false'},
                               topics=['device/#'])
            matcher.assert_called_once_with('device/#', 'device/commands')
        self.data['home_assistant'] = ha
        self.assertEqual(ha['discovery_base'], 'custom/ha/button/mqtt_listener_test-device/')
        self.discover()
        calls = self.client.publish.call_args_list
        self.assertTrue(all(not c.kwargs['retain'] for c in calls[:-1]))
        self.assertEqual(calls[-1].args, ('custom/availability',))
        self.assertTrue(calls[-1].kwargs['retain'])
        self.assertIsNone(self.settings(topics=['device/#']))

    def test_connect_reconnect_and_refused_connection(self):
        for rc in (0, 0):
            self.listener['on_connect'](self.client, self.data, {}, rc)
        self.assertEqual(self.client.publish.call_count, 8)
        self.assertEqual(sum(c.args == ('homeassistant/status',) for c in self.client.subscribe.call_args_list), 2)
        self.client.reset_mock()
        self.listener['on_connect'](self.client, self.data, {}, 5)
        self.client.publish.assert_not_called()
        self.assertNotIn(('homeassistant/status',), [c.args for c in self.client.subscribe.call_args_list])

    def test_ha_birth_ignores_retained_replay_and_republishes_fresh_birth(self):
        self.data['commands']['online'] = 'should only execute on command topic'

        # Reproduce startup ordering: on_connect publishes discovery once, then
        # the broker may replay retained homeassistant/status=online. That replay
        # must not cause a second discovery snapshot.
        self.listener['on_connect'](self.client, self.data, {}, 0)
        self.assertEqual(len(self.buttons()), 4)
        initial_publish_count = self.client.publish.call_count
        self.message('homeassistant/status', b'online', retained=True)
        self.assertEqual(self.client.publish.call_count, initial_publish_count)
        self.launch.assert_not_called()

        self.client.reset_mock()
        self.message('homeassistant/status', b'online', retained=False)
        self.assertEqual(len(self.buttons()), 4)
        self.launch.assert_not_called()
        self.client.reset_mock()
        for payload in (b'offline', b'\xff', b' online '):
            self.message('homeassistant/status', payload)
        self.client.publish.assert_not_called()
        self.launch.assert_not_called()
        self.data['home_assistant']['status_online_payload'] = 'ready'
        self.message('homeassistant/status', b'ready')
        self.assertEqual(len(self.buttons()), 4)

    def test_metadata_is_reserved_before_decoding_with_broad_subscriptions(self):
        ha = self.data['home_assistant']
        for topic in (ha['status_topic'], ha['availability_topic'], ha['discovery_base']+'x/config'):
            for payload in (b'shutdown_delay', b'\xff'):
                self.message(topic, payload, retained=True)
        self.launch.assert_not_called()
        self.client.publish.assert_not_called()
        # Original commands remain available on their original topic, even 'online'.
        self.data['commands']['online'] = 'echo original'
        self.message('device/commands', b'online')
        self.launch.assert_called_once_with('echo original', shell=True)

    def test_announcement_and_discovery_coexist(self):
        self.data['online_topic'] = 'device/status'
        self.listener['on_connect'](self.client, self.data, {}, 0)
        first = self.client.publish.call_args_list[0]
        self.assertEqual(first.args, ('device/status',))
        self.assertEqual(first.kwargs, dict(payload='online', qos=1, retain=False))
        self.assertEqual(len(self.buttons()), 3)
        self.message('device/status', b'shutdown_delay')
        self.launch.assert_not_called()

    def test_publish_errors_do_not_stop_remaining_discovery_or_commands(self):
        self.client.publish.side_effect = [OSError('simulated'), types.SimpleNamespace(rc=4),
                                           types.SimpleNamespace(rc=0), types.SimpleNamespace(rc=0)]
        self.discover()
        self.assertEqual(self.client.publish.call_count, 4)
        self.assertIn('simulated', self.logs.getvalue())
        self.assertIn('could not be queued', self.logs.getvalue())
        self.message('device/commands', b'shutdown_delay')
        self.launch.assert_called_once_with('/trusted/power.sh', shell=True)

    def test_birth_subscription_error_still_publishes_discovery(self):
        for failure in (OSError('simulated'), (4, None)):
            self.client.reset_mock(side_effect=True)
            self.client.subscribe.side_effect = [(0, 1), (0, 2), failure]
            self.listener['on_connect'](self.client, self.data, {}, 0)
            self.assertEqual(len(self.buttons()), 3)

    def test_main_configures_last_will_before_connect_and_reuses_callbacks(self):
        constructor, _ = test_listener.ListenerTests().run_cli(['-c', 'x'],
            'topics: device/commands\nha_enabled: true\nha_device_id: test-device\n'
            'ha_device_name: My Server\ncommands:\nping = echo safe\n')
        client = constructor.return_value
        client.will_set.assert_called_once_with('mqtt-listener/test-device/availability',
                                               payload='offline', qos=1, retain=True)
        calls = [call[0] for call in client.mock_calls]
        self.assertLess(calls.index('will_set'), calls.index('connect'))
        self.assertEqual(client.on_connect.__name__, 'on_connect')
        self.assertEqual(client.on_message.__name__, 'on_message')
        client.publish.assert_not_called()

    def test_topic_validation_handles_utf8_byte_limit(self):
        validate = self.listener['valid_publish_topic']
        for topic in ('', '+', 'a/#', 'bad\x00topic', 'æ'*32768):
            self.assertFalse(validate(topic))
        self.assertTrue(validate('æ'*32767))


if __name__ == '__main__':
    unittest.main()
