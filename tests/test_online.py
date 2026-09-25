"""Check announcements and command isolation without broker/process effects."""
import contextlib
import io
import types
import unittest
from unittest.mock import MagicMock, patch

import test_listener
from test_listener import load_listener


class OnlineTests(unittest.TestCase):
    def setUp(self):
        self.listener = load_listener()
        self.data = {'topics': ['device/#'], 'commands': {'online': 'echo mapped'},
                     'online_topic': 'device/status'}
        self.client = MagicMock()
        self.client.publish.return_value.rc = 0

    def connect(self, rc=0):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.listener['on_connect'](self.client, self.data, {}, rc)
        return output.getvalue()

    def test_online_on_successful_connect_and_reconnect(self):
        for _ in range(2):
            self.connect()
        self.assertEqual(self.client.publish.call_count, 2)
        self.client.publish.assert_called_with('device/status', payload='online', qos=1, retain=False)
        self.assertEqual(self.client.subscribe.call_count, 2)
        self.client.publish.return_value.wait_for_publish.assert_not_called()

    def test_refused_connection_does_not_announce(self):
        self.connect(rc=5)
        self.client.publish.assert_not_called()

    def test_missing_online_topic_preserves_legacy_behavior(self):
        del self.data['online_topic']
        self.connect()
        self.client.subscribe.assert_called_once_with('device/#')
        self.client.publish.assert_not_called()

    def test_announcement_errors_do_not_stop_callback(self):
        self.client.publish.side_effect = OSError('simulated')
        self.assertIn('Failed to announce online: simulated', self.connect())
        self.client.subscribe.assert_called_once_with('device/#')

    def test_publish_error_result_is_logged(self):
        self.client.publish.return_value.rc = 4
        self.assertIn('could not be queued: 4', self.connect())

    def test_status_topic_is_ignored_before_decoding_or_command_lookup(self):
        for payload in (b'online', b'\xff'):
            with self.subTest(payload=payload), patch.object(self.listener['subprocess'], 'Popen') as launch:
                self.listener['on_message'](None, self.data,
                    types.SimpleNamespace(topic='device/status', payload=payload))
                launch.assert_not_called()

    def test_online_remains_a_command_on_original_command_topics(self):
        with patch.object(self.listener['subprocess'], 'Popen') as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            self.listener['on_message'](None, self.data,
                types.SimpleNamespace(topic='device/commands', payload=b'online'))
        launch.assert_called_once_with('echo mapped', shell=True)

    def test_validation_disables_invalid_and_exact_conflicting_topics(self):
        for topic in ('device/#', 'device/+', 'bad\x00topic', 'x' * 65536, 'device/commands'):
            with self.subTest(topic=topic[:30]), contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(self.listener['get_online_topic'](
                    {'online_topic': topic}, ['device/commands']))

    def test_missing_or_blank_topic_disables_feature(self):
        for config in ({}, {'online_topic': '   '}):
            self.assertIsNone(self.listener['get_online_topic'](config, ['device/commands']))

    def test_valid_topic_with_wildcard_subscription_is_reserved(self):
        self.assertEqual(self.listener['get_online_topic'](
            {'online_topic': ' device/status '}, ['device/#']), 'device/status')

    def test_main_adds_only_valid_online_topic_to_userdata(self):
        helper = test_listener.ListenerTests()
        constructor, _ = helper.run_cli(['-c', 'x'],
            'topics: device/commands\nonline_topic: device/status\ncommands:\n\tonline = echo mapped\n')
        constructor.assert_called_once_with(userdata={'topics': ['device/commands'],
            'online_topic': 'device/status', 'commands': {'online': 'echo mapped'}})

    def test_tabs_and_spaces_parse_identically(self):
        helper = test_listener.ListenerTests()
        helper.setUp()
        self.assertEqual(helper.parse('commands:\n\tping = echo safe\n'),
                         helper.parse('commands:\n    ping = echo safe\n'))


if __name__ == '__main__':
    unittest.main()
