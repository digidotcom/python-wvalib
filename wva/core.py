# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from wva.http_client import WVAHttpClient
from wva.stream import WVAEventStream
from wva.subscriptions import WVASubscription
from wva.vehicle import VehicleDataElement


class WVA(object):
    def __init__(self, hostname, username, password, use_https=True):
        self._http_client = WVAHttpClient(hostname, username, password, use_https)
        self._event_stream = None

    @property
    def hostname(self):
        return self._http_client.hostname

    @hostname.setter
    def hostname(self, hostname):
        self._http_client._hostname = hostname

    @property
    def username(self):
        return self._http_client.username

    @username.setter
    def username(self, username):
        self._http_client.username = username

    @property
    def password(self):
        return self._http_client.password

    @password.setter
    def password(self, password):
        self._http_client.password = password

    @property
    def use_https(self):
        return self._http_client.use_https

    @use_https.setter
    def use_https(self, use_https):
        self._http_client.use_https = use_https

    def get_http_client(self):
        """Get a direct reference to the http client used by this WVA instance"""
        return self._http_client

    def get_vehicle_data_element(self, name):
        """Return a :class:`VehicleDataElement` with the given name

        For example, if I wanted to get information about the speed of a vehicle,
        I could do so by doing the following::

            speed = wva.get_vehicle_data_element("VehicleSpeed")
            print(speed.get_value())
        """
        return VehicleDataElement(self._http_client, name)


    def get_vehicle_data_elements(self):
        """Get a dictionary mapping names to :class:`VehicleData` instances

        This result is based on the results of `GET /ws/vehicle/data` that returns a list
        of URIs to each vehicle data element.  The value is a handle for accessing
        additional information about a particular data element.

        :raises WVAError: In the event of a problem retrieving the list of data elements
        :returns: A dictionary of element names mapped to :class:`VehicleDataElement` instances.
        """
        # Response looks like: { "data": ['vehicle/data/ParkingBrake', ...] }
        elements = {}
        for uri in self.get_http_client().get("vehicle/data").get("data", []):
            name = uri.split("/")[-1]
            elements[name] = self.get_vehicle_data_element(name)
        return elements

    def get_subscription(self, short_name):
        """Get the subscription with the provided short_name

        :returns: A :class:`WVASubscription` instance bound for the specified short name
        """
        return WVASubscription(self._http_client, short_name)

    def get_subscriptions(self):
        """Return a list of subscriptions currently active for this WVA device

        :raises WVAError: if there is a problem getting the subscription list from the WVA
        :returns: A list of :class:`WVASubscription` instances
        """
        # Example: {'subscriptions': ['subscriptions/TripDistance~sub', 'subscriptions/FuelRate~sub', ]}
        subscriptions = []
        for uri in self.get_http_client().get("subscriptions").get('subscriptions'):
            subscriptions.append(self.get_subscription(uri.split("/")[-1]))
        return subscriptions

    def get_event_stream(self):
        """Get the event stream associated with this WVA

        Note that this event stream is shared across all users of this WVA device
        as the WVA only supports a single event stream.

        :return: a new :class:`WVAEventStream` instance
        """
        if self._event_stream is None:
            self._event_stream = WVAEventStream(self._http_client)
        return self._event_stream
