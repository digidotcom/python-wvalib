# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

import json
import logging

import socket
import threading
import time
import six
from wva.exceptions import WVAError


logger = logging.getLogger(__name__)

EVENT_STREAM_STATE_DISABLED = "EVENT_STREAM_STATE_DISABLED"
EVENT_STREAM_STATE_CONNECTING = "EVENT_STREAM_STATE_CONNECTING"
EVENT_STREAM_STATE_CONNECTED = "EVENT_STREAM_STATE_CONNECTED"

DELAY_ON_ERROR = 0.5
SOCKET_TIMEOUT = 0.5


class WVAEventStream(object):
    """Provide methods for working with the event stream from a WVA Device"""

    def __init__(self, http_client):
        self._http_client = http_client
        self._event_listeners = set()
        self._event_listener_thread = None
        self._lock = threading.RLock()

    def emit_event(self, event):
        """Emit the specified event (notify listeners)"""
        with self._lock:
            listeners = list(self._event_listeners)

        for cb in list(self._event_listeners):
            # noinspection PyBroadException
            try:
                cb(event)
            except:
                # Don't let exceptions from callbacks kill our thread of execution
                logger.exception("Event callback resulted in unhandled exception")

    def enable(self):
        """Enable the stream thread

        This operation will ensure that the thread that is responsible
        for connecting to the WVA and triggering event callbacks is started.
        This thread will continue to run and do what it needs to do to
        maintain a connection to the WVA.

        The status of the thread can be monitored by calling :meth:`get_status`.
        """
        with self._lock:
            if self._event_listener_thread is None:
                self._event_listener_thread = WVAEventListenerThread(self, self._http_client)
                self._event_listener_thread.start()

    def disable(self):
        """Disconnect from the event stream"""
        with self._lock:
            if self._event_listener_thread is not None:
                self._event_listener_thread.stop()
                self._event_listener_thread = None

    def get_status(self):
        """Get the current status of the event stream system

        The status will be one of the following:

        - EVENT_STREAM_STATE_STOPPED: if the stream thread has not been enabled
        - EVENT_STREAM_STATE_CONNECTING: the stream thread is running and
            attempting to establish a connection to the WVA to receive events.
        - EVENT_STREAM_STATE_CONNECTED: We are connected to the WVA and
            receiving or ready to receive events.  If no events are being
            received, one should verify that vehicle data is being received
            and there is an appropriate set of subscriptions set up.
        """
        with self._lock:
            if self._event_listener_thread is None:
                return EVENT_STREAM_STATE_DISABLED
            else:
                return self._event_listener_thread.get_state()

    def add_event_listener(self, callback):
        """Add a listener that will be called when events are received

        This callback will be called when any event is received.  The callback
        will be called as follows and should have an appropriate shape::

            callback(event)

        Where event is a dictionary containg the event data as described in
        the `WVA Documentation on Events <http://goo.gl/6vU5i1>`_.

        .. note::

           The event stream operates in its own thread of execution and event callbacks
           will occur on the event stream thread.  In order to avoid delay of delivery
           of other events, one should avoid blocking in the callback.  If there is
           a large amount of work to do, it may make sense to use a Queue to pass
           the event on to another thread of execution.

        """
        with self._lock:
            self._event_listeners.add(callback)

    def remove_event_listener(self, callback):
        """Remove the provided event listener callback"""
        with self._lock:
            self._event_listeners.remove(callback)


class WVAEventListenerThread(threading.Thread):
    """Thread responsible for communicating with WVA in order to receive a stream of events"""

    def __init__(self, event_stream, http_client):
        threading.Thread.__init__(self, name="WVAEventListenerThread")
        self.setDaemon(True)
        self._event_stream = event_stream
        self._http_client = http_client
        self._socket = None
        self._buf = six.u('')
        self._stop_requested = False
        self._decoder = json.JSONDecoder()
        self._state = EVENT_STREAM_STATE_CONNECTING
        self._state_map = {
            EVENT_STREAM_STATE_CONNECTING: self._service_connecting,
            EVENT_STREAM_STATE_CONNECTED: self._service_connected,
        }

    @staticmethod
    def _create_connected_socket(host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((host, port))
        return sock

    def _parse_one_event(self):
        """Parse the stream buffer and return either a single event or None"""
        # WVA includes \r\n between messages which the parser doesn't like, so we
        # throw away any data before a opening brace
        try:
            open_brace_idx = self._buf.index('{')
        except ValueError:
            self._buf = six.u('')  # no brace found
        else:
            if open_brace_idx > 0:
                self._buf = self._buf[open_brace_idx:]

        try:
            event, idx = self._decoder.raw_decode(self._buf)
            self._buf = self._buf[idx:]
            return event
        except ValueError:
            return None

    def _service_connecting(self):
        # noinspection PyBroadException
        try:
            # get event info and enable if not enabled currently
            event_info = self._http_client.get("config/ws_events")["ws_events"]
            if event_info["enable"] != "on":
                # enable events
                self._http_client.put("config/ws_events", {
                    "enable": "on",
                    "port": event_info["port"],  # just keep existing port
                })
            host = self._http_client.hostname
            port = event_info["port"]
            self._socket = self._create_connected_socket(host, port)
        except WVAError as e:
            logger.debug("WVAError connecting to event stream: %s", e)
            time.sleep(DELAY_ON_ERROR)
        except socket.error as e:
            logger.debug("socket.error connecting to event stream: %s", e)
            time.sleep(DELAY_ON_ERROR)
        except:
            logger.exception("Unexpected exception")
        else:
            self._buf = six.u('')  # ensure buffer is emptied
            self._state = EVENT_STREAM_STATE_CONNECTED

    def _service_connected(self):
        # grab new data
        try:
            data = self._socket.recv(1024)
        except socket.timeout:
            return
        except socket.error as e:
            logger.debug("socket.error from connected state: %s", e)
            logger.info("Connected -> Connecting (socket error)")
            self._socket.close()
            self._state = EVENT_STREAM_STATE_CONNECTING
            return

        if not data:
            logger.info("Connect -> Connecting (EOF)")
            self._socket.close()
            self._state = EVENT_STREAM_STATE_CONNECTING
            return
        else:
            self._buf += data.decode('utf-8')
            while True:
                event = self._parse_one_event()
                if event is None:
                    break
                else:
                    self._event_stream.emit_event(event)

    def _step(self):
        service_fn = self._state_map[self._state]
        service_fn()

    def get_state(self):
        """Get the current state"""
        return self._state

    def stop(self):
        """Request that the event stream thread be stopped and wait for it to stop"""
        self._stop_requested = True
        self.join()

    def run(self):
        while not self._stop_requested:
            self._step()

        if self._socket is not None:
            self._socket.close()
