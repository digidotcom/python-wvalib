# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from wva.http_client import WVAHttpClient
from wva.vehicle import VehicleDataElement


class WVA(object):
    def __init__(self, hostname, username, password, use_https=True):
        self._http_client = WVAHttpClient(hostname, username, password, use_https)

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
