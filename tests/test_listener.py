"""Offline contracts for unchanged listener code; no broker or real subprocesses."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import MagicMock, mock_open, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'mqtt-listener.py'


def fake_paho():
    """Supply a minimal module hierarchy and observable, inert MQTT client."""
    paho = types.ModuleType('paho')
    mqtt = types.ModuleType('paho.mqtt')
    client = types.ModuleType('paho.mqtt.client')
    client.Client = MagicMock(name='Client')
    client.MQTT_ERR_SUCCESS = 0
    paho.mqtt = mqtt
    mqtt.client = client
    return {'paho': paho, 'paho.mqtt': mqtt, 'paho.mqtt.client': client}, client


def load_listener():
    """Import real functions without running the guarded main block."""
    modules, _ = fake_paho()
    with patch.dict(sys.modules, modules):
        return runpy.run_path(str(SCRIPT), run_name='listener_under_test')


class ListenerTests(unittest.TestCase):
    def setUp(self):
        self.listener = load_listener()

    def parse(self, text):
        with patch('builtins.open', mock_open(read_data=text)):
            return self.listener['read_config']('in-memory.txt')

    def run_cli(self, argv, config=''):
        modules, mqtt = fake_paho()
        output = io.StringIO()
        with patch.dict(sys.modules, modules), \
                patch.object(sys, 'argv', [str(SCRIPT), *argv]), \
                patch('builtins.open', mock_open(read_data=config)), \
                contextlib.redirect_stdout(output), \
                contextlib.redirect_stderr(output):
            runpy.run_path(str(SCRIPT), run_name='__main__')
        return mqtt.Client, output.getvalue()

    def message(self, payload, mapping, *, retained=False, error=None):
        msg = types.SimpleNamespace(payload=payload, topic='test/actions', retain=retained)
        output = io.StringIO()
        with patch.object(self.listener['subprocess'], 'Popen', side_effect=error) as launch, \
                contextlib.redirect_stdout(output):
            self.listener['on_message'](None, {'commands': mapping}, msg)
        self.last_message_output = output.getvalue()
        return launch

    def test_config_comments_trimming_and_first_equals(self):
        config = self.parse('  # comment\n\nhostname: broker\ntopics: one, two\ncommands:\n  ping = echo A=B  \n')
        self.assertEqual(config, {'hostname': 'broker', 'topics': 'one, two',
                                  'commands': {'ping': 'echo A=B'}})

    def test_config_duplicates_use_last_value(self):
        config = self.parse('hostname: first\nhostname: second\ncommands:\nx = one\nx = two\n')
        self.assertEqual(config['hostname'], 'second')
        self.assertEqual(config['commands'], {'x': 'two'})

    def test_config_empty_value_is_section_and_inline_comments_remain(self):
        config = self.parse('username:\nport: 1883 # inline\n')
        self.assertNotIn('username', config)
        self.assertEqual(config['port'], '1883 # inline')

    def test_example_has_every_setting_and_original_payload(self):
        config = self.listener['read_config'](str(ROOT / 'commands-example.txt'))
        self.assertEqual(set(config), {'hostname', 'port', 'username', 'password', 'topics', 'online_topic', 'commands'})
        self.assertEqual(set(config['commands']),
                         {'shutdown_delay', 'shutdown_cancel', 'reboot_delay', 'reboot_cancel'})
        for command in config['commands'].values():
            self.assertTrue((ROOT / Path(command).name).is_file())

    def test_message_trims_and_launches_only_configured_command(self):
        launch = self.message(b'  ping\n', {'ping': 'echo safe'})
        launch.assert_called_once_with('echo safe', shell=True)

    def test_unknown_case_mismatch_and_shell_payload_do_not_launch(self):
        for payload in (b'unknown', b'PING', b'ping; reboot'):
            with self.subTest(payload=payload):
                self.message(payload, {'ping': 'echo safe'}).assert_not_called()

    def test_empty_command_does_not_launch(self):
        self.message(b'ping', {'ping': ''}).assert_not_called()

    def test_retained_and_repeated_messages_are_not_filtered(self):
        for _ in range(2):
            self.message(b'ping', {'ping': 'echo safe'}, retained=True).assert_called_once()

    def test_launch_error_is_logged_without_escaping_callback(self):
        self.message(b'ping', {'ping': 'echo safe'}, error=OSError('simulated')).assert_called_once()
        self.assertIn('Failed to execute command: simulated', self.last_message_output)

    def test_invalid_utf8_raises_before_launch(self):
        with patch.object(self.listener['subprocess'], 'Popen') as launch:
            with self.assertRaises(UnicodeDecodeError):
                self.listener['on_message'](None, {'commands': {}},
                                          types.SimpleNamespace(payload=b'\xff', topic='test'))
            launch.assert_not_called()

    def test_connect_requests_each_topic_even_on_failure_code(self):
        for rc in (0, 5):
            with self.subTest(rc=rc), contextlib.redirect_stdout(io.StringIO()):
                client = MagicMock()
                self.listener['on_connect'](client, {'topics': ['one', 'two']}, {}, rc)
                self.assertEqual([call.args for call in client.subscribe.call_args_list], [('one',), ('two',)])

    def test_main_passes_config_to_client_and_registers_callbacks(self):
        constructor, _ = self.run_cli(['--config', 'config.txt'],
            'hostname: broker\nport: 1884\nusername: user\npassword: secret\n'
            'topics: one, two\ncommands:\nping = echo safe\n')
        constructor.assert_called_once_with(userdata={'topics': ['one', 'two'], 'commands': {'ping': 'echo safe'}})
        client = constructor.return_value
        client.username_pw_set.assert_called_once_with('user', 'secret')
        client.connect.assert_called_once_with('broker', 1884, 60)
        client.loop_forever.assert_called_once_with()
        self.assertEqual(client.on_connect.__name__, 'on_connect')
        self.assertEqual(client.on_message.__name__, 'on_message')

    def test_main_defaults_and_incomplete_credentials_skip_auth(self):
        for config in ('', 'username: user\n', 'password: secret\n'):
            with self.subTest(config=config):
                constructor, _ = self.run_cli(['-c', 'config.txt'], config)
                constructor.assert_called_once_with(userdata={'topics': [''], 'commands': {}})
                constructor.return_value.connect.assert_called_once_with('localhost', 1883, 60)
                constructor.return_value.username_pw_set.assert_not_called()

    def test_help_exits_zero_and_lists_flags_without_creating_client(self):
        for flag in ('-h', '--help'):
            modules, mqtt = fake_paho()
            output = io.StringIO()
            with patch.dict(sys.modules, modules), patch.object(sys, 'argv', [str(SCRIPT), flag]), \
                    contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(SCRIPT), run_name='__main__')
            self.assertEqual(caught.exception.code, 0)
            self.assertIn('-c CONFIG, --config CONFIG', output.getvalue())
            self.assertIn('-h, --help', output.getvalue())
            mqtt.Client.assert_not_called()

    def test_missing_config_unknown_flag_and_missing_value_exit_two(self):
        for argv in ([], ['-c'], ['-c', 'x', '--dry-run'], ['--version']):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as caught:
                self.run_cli(argv)
            self.assertEqual(caught.exception.code, 2)

    def test_invalid_port_raises(self):
        with self.assertRaises(ValueError):
            self.run_cli(['-c', 'x'], 'port: invalid\n')

    def test_missing_config_file_raises(self):
        with patch('builtins.open', side_effect=FileNotFoundError('simulated')):
            with self.assertRaises(FileNotFoundError):
                self.listener['read_config']('missing.txt')


if __name__ == '__main__':
    unittest.main()
