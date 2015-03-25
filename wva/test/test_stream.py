# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json
import socket
import _socket
import unittest
import time
import mock
import six
from wva.stream import WVAEventListenerThread, EVENT_STREAM_STATE_CONNECTING, EVENT_STREAM_STATE_CONNECTED, \
    EVENT_STREAM_STATE_DISABLED

from wva.test.test_utilities import WVATestBase


class TestWVAEventStream(WVATestBase):
    def setUp(self):
        WVATestBase.setUp(self)
        self.prepare_response("GET", "/ws/config/ws_events", status=500)  # error by default

        # httpretty breaks socketpair on py3, so workaround by using _socket directly
        self.sock_head, self.sock_tail = _socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)

    def tearDown(self):
        WVATestBase.tearDown(self)
        self.sock_head.close()
        self.sock_tail.close()

    def _mock_create_connected_socket(self, host, port):
        return self.sock_tail

    def _get_event_listener_thread(self):
        listener_thread = WVAEventListenerThread(
            self.wva.get_event_stream(),
            self.wva.get_http_client(),
        )

        # Swap in the tail of our socket pair
        listener_thread._create_connected_socket = self._mock_create_connected_socket
        return listener_thread

    def _prepare_event_stream(self):
        self.prepare_json_response(
            "GET", "/ws/config/ws_events",
            {'ws_events': {'enable': 'on', 'port': 5000}}
        )

    def test_callback_exception_caught(self):
        def raiser(evt):
            raise ValueError("Something went wrong")

        # Tests will fail if exception is raised
        cb = mock.Mock(side_effect=raiser)
        self.wva.get_event_stream().add_event_listener(raiser)
        self.wva.get_event_stream().emit_event({})

    def test_enable_disable(self):
        stream = self.wva.get_event_stream()
        self.assertEqual(stream.get_status(), EVENT_STREAM_STATE_DISABLED)
        elt = mock.Mock()
        with mock.patch('wva.stream.WVAEventListenerThread', return_value=elt) as ELT:
            stream.enable()
            stream.enable()  # call a second time to ensure only called  once still
            ELT.assert_called_once_with(stream, stream._http_client)
            elt.start.assert_called_once_with()
            elt.get_state = lambda: EVENT_STREAM_STATE_CONNECTING
            self.assertEqual(stream.get_status(), EVENT_STREAM_STATE_CONNECTING)

        stream.disable()
        stream.disable()  # should be set to None and only called once
        elt.stop.assert_called_once_with()

    def test_add_callback(self):
        event_stream = self.wva.get_event_stream()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        event_stream.emit_event({"testing": [1, 2, 3]})
        cb.assert_called_once_with({"testing": [1, 2, 3]})

    def test_remove_callback(self):
        event_stream = self.wva.get_event_stream()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        event_stream.remove_event_listener(cb)
        event_stream.emit_event({"testing": [1, 2, 3]})
        cb.assert_has_calls([])  # not called

    @mock.patch('time.sleep', return_value=None)
    def test_wva_error_on_connect_and_then_success(self, mock_sleep):
        listener_thread = self._get_event_listener_thread()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        listener_thread._step()
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        self.assertEqual(mock_sleep.call_count, 3)

    @mock.patch('time.sleep', return_value=None)
    def test_socket_error_on_connecting(self, mock_sleep):
        def _failing_socket_connect(host, port):
            raise socket.error("connect failure")

        self._prepare_event_stream()  # Can talk to the WVA fine
        listener_thread = self._get_event_listener_thread()
        listener_thread._create_connected_socket = _failing_socket_connect
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        listener_thread._step()
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        self.assertEqual(mock_sleep.call_count, 3)

    def test_socket_timeout_when_connected(self):
        # This is a normal occurrence, and it should not cause any state transition
        self._prepare_event_stream()
        event_stream = self.wva.get_event_stream()
        listener_thread = self._get_event_listener_thread()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTED)

        # replace socket with mock that will raise socket.timeout
        def recv_raise_timeout(size):
            raise socket.timeout("this is pretty normal")
        listener_thread._socket = mock.Mock()
        listener_thread._socket.recv = recv_raise_timeout

        # do recv and ensure no exceptions and no state transition
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTED)

    def test_socket_error_when_connected(self):
        self._prepare_event_stream()
        event_stream = self.wva.get_event_stream()
        listener_thread = self._get_event_listener_thread()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTED)

        # replace socket with mock that will raise socket.timeout
        def recv_raise_error(size):
            raise socket.error("Something bad happened")
        mock_sock = mock.Mock()
        listener_thread._socket = mock_sock
        listener_thread._socket.recv = recv_raise_error

        # do recv and ensure no exceptions and no state transition
        listener_thread._step()
        mock_sock.close.assert_called_once_with()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)

    def test_socket_eof_when_connected(self):
        self._prepare_event_stream()
        event_stream = self.wva.get_event_stream()
        listener_thread = self._get_event_listener_thread()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTED)

        # close the head of the socket pair to force an EOF
        self.sock_head.close()

        # do recv and ensure no exceptions and no state transition
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)

    def test_thread_start_stop(self):
        # NOTE: without doing any additional work, web service calls will
        # fail, so we do not need to worry about anything hitting the
        # live network
        #
        # This test exists mostly to get coverage on a few parts of the main loop
        # for the thread
        with mock.patch('time.sleep', return_value=None):
            stream = self.wva.get_event_stream()
            stream.enable()
            elt = stream._event_listener_thread
            time.sleep(0.01)
            self.assertTrue(elt.isAlive())
            stream.disable()
            self.assertIsNone(stream._event_listener_thread)
            self.assertFalse(elt.isAlive())

    def test_happy_path(self):
        self._prepare_event_stream()
        event_stream = self.wva.get_event_stream()
        listener_thread = self._get_event_listener_thread()

        cb = mock.Mock()
        event_stream.add_event_listener(cb)
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTING)
        listener_thread._step()
        self.assertEqual(listener_thread.get_state(), EVENT_STREAM_STATE_CONNECTED)
        event = {'data': {'VehicleSpeed': {'timestamp': '2015-03-22T05:14:31Z',
                                           'value': 153.095673},
                          'sequence': 99649,
                          'short_name': 'speedy',
                          'timestamp': '2015-03-22T05:14:31Z',
                          'uri': 'vehicle/data/VehicleSpeed'}}
        event2 = {'data': {'VehicleSpeed': {'timestamp': '2015-03-22T05:14:30Z',
                                            'value': 155.607224},
                           'sequence': 99648,
                           'short_name': 'speedy',
                           'timestamp': '2015-03-22T05:14:30Z',
                           'uri': 'vehicle/data/VehicleSpeed'}}
        self.sock_head.send(six.b(json.dumps(event) + '\r\n' + json.dumps(event2)))
        listener_thread._step()
        cb.assert_has_calls([
            mock.call(event),
            mock.call(event2),
        ])


if __name__ == '__main__':
    unittest.main()
