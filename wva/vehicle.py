# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from collections import namedtuple
import arrow

VehicleDataSample = namedtuple('VehicleDataSample', ['value', 'timestamp'])


class VehicleDataElement(object):
    """Provides access to a particular vehicle data element"""

    def __init__(self, http_client, element_name):
        self.name = element_name
        self._http_client = http_client

    def sample(self):
        """Get the current value of this vehicle data element

        The returned value will be a namedtuple with 'value' and
        'timestamp' elements.  Example::

            speed_el = wva.get_vehicle_data_element('VehicleSpeed')
            for i in xrange(10):
                speed = speed_el.sample()
                print("Speed: %0.2f @ %s" % (speed.value, speed.timestamp))
                time.sleep(1)
        """
        # Response: {'VehicleSpeed': {'timestamp': '2015-03-20T18:00:49Z', 'value': 223.368515}}
        data = self._http_client.get("vehicle/data/{}".format(self.name))[self.name]
        dt = arrow.get(data["timestamp"]).datetime
        value = data["value"]
        return VehicleDataSample(value, dt)
