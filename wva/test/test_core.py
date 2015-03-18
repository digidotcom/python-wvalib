# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

import json
import unittest
import httpretty
import six.moves.urllib.parse as urllib_parse
from wva import WVA


class WVATestBase(unittest.TestCase):

    def setUp(self):
        httpretty.enable()
        # setup the Device cloud ping response
        self.wva = WVA("192.168.100.1", "user", "pass")

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def _get_last_request(self):
        return httpretty.last_request()

    def _get_last_request_params(self):
        # Get the query params from the last request as a dictionary
        params = urllib_parse.parse_qs(urllib_parse.urlparse(self._get_last_request().path).query)
        return {k: v[0] for k, v in params.items()}  # convert from list values to single-value

    def prepare_response(self, method, path, data=None, status=200, match_querystring=False, **kwargs):
        if data is not None:
            kwargs['body'] = data
        httpretty.register_uri(method,
                               "https://192.168.100.1{}".format(path),
                               match_querystring=match_querystring,
                               status=status,
                               **kwargs)

    def prepare_json_response(self, method, path, data, status=200):
        headers = {'content-type': 'application/json'}
        self.prepare_response(method, path, json.dumps(data), status=status, **headers)


class TestWVABasicRequestMethods(WVATestBase):

    def test_json_get(self):
        self.prepare_json_response("GET", "/ws/testing/1/2/3", {
            "this": "is a test"
        })
        self.assertEqual(self.wva.get("testing/1/2/3"), {"this": "is a test"})
        self._get_last_request()

    def test_xml_get(self):
        self.prepare_response("GET", "/ws/testing/1/2/3", "A RESPONSE")
        self.assertEqual(self.wva.get("testing/1/2/3"), "A RESPONSE")

    def test_json_post(self):
        self.prepare_json_response("POST", "/ws/post", {"error": "an error"})
        self.assertEqual(self.wva.post("post", {"my": "post request"}), {"error": "an error"})
        self.assertEqual(self._get_last_request().body, '{"my": "post request"}')
