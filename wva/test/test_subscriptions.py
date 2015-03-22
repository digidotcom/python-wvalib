# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json

from wva.test.test_utilities import WVATestBase


class TestWVASubscriptions(WVATestBase):

    def test_get_subscriptions(self):
        self.prepare_json_response("GET", "/ws/subscriptions", {
            "subscriptions": [
                "subscriptions/a",
                "subscriptions/b",
            ]
        })
        subs = self.wva.get_subscriptions()
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].short_name, "a")
        self.assertEqual(subs[1].short_name, "b")

    def test_get_metadata(self):
        self.prepare_json_response("GET", "/ws/subscriptions/speedy", {
            'subscription': {'buffer': 'queue',
                             'interval': 1,
                             'uri': 'vehicle/data/VehicleSpeed'}
        })
        sub = self.wva.get_subscription("speedy")
        self.assertEqual(sub.get_metadata(), {
            'buffer': 'queue',
            'interval': 1,
            'uri': 'vehicle/data/VehicleSpeed',
        })

    def test_delete(self):
        self.prepare_response("DELETE", "/ws/subscriptions/short-name", "")
        sub = self.wva.get_subscription("short-name")
        sub.delete()
        self.assertEqual(self._get_last_request().method, "DELETE")
        self.assertEqual(self._get_last_request().path, "/ws/subscriptions/short-name")

    def test_create(self):
        self.prepare_response("PUT", "/ws/subscriptions/new-short-name", "")
        sub = self.wva.get_subscription("new-short-name")
        sub.create("vehicle/data/EngineSpeed", buffer="drop", interval=5)
        req = self._get_last_request()
        self.assertDictEqual(json.loads(req.body.decode('utf-8')), {
            'subscription': {'buffer': 'drop',
                             'interval': 5,
                             'uri': 'vehicle/data/EngineSpeed'},
        })
