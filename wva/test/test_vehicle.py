# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

import datetime
from dateutil.tz import tzutc
from wva.test.test_utilities import WVATestBase


class TestVehicleDataElement(WVATestBase):
    def test_get_vehicle_data_elements(self):
        self.prepare_json_response("GET", "/ws/vehicle/data",
                                   {
                                       'data': [
                                           'vehicle/data/ParkingBrake',
                                           'vehicle/data/VehicleSpeed',  # real one has way more...
                                       ]
                                   })
        els = self.wva.get_vehicle_data_elements()
        self.assertEqual(len(els), 2)
        self.assertEqual(set(els.keys()), {'ParkingBrake', 'VehicleSpeed'})
        self.assertEqual(els["ParkingBrake"].name, "ParkingBrake")
        self.assertEqual(els["ParkingBrake"].name, "ParkingBrake")

    def test_sample(self):
        self.prepare_json_response("GET", "/ws/vehicle/data/VehicleSpeed",
                                   {'VehicleSpeed':
                                        {
                                            'timestamp': '2015-03-20T20:11:10Z',
                                            'value': 170.664856
                                        }
                                   })
        el = self.wva.get_vehicle_data_element("VehicleSpeed")
        sample = el.sample()
        self.assertAlmostEqual(sample.value, 170.664856)
        self.assertEqual(sample.timestamp, datetime.datetime(2015, 3, 20, 20, 11, 10, tzinfo=tzutc()))
