# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import base64

import httpretty
import six
from wva.test.test_utilities import WVATestBase


class TestWVAHttpClient(WVATestBase):
    def _get_username_pass(self, request):
        authorization = request.headers.get("authorization")  # e.g. "Basic <base64>"
        b64encoded = six.b(authorization.split(" ", 1)[1])  # e.g. user:pass
        return base64.b64decode(b64encoded).split(six.b(":"))

    def _perform_simple_request(self):
        self.prepare_response("GET", "/ws/test", "Value")
        self.assertEqual(self.wva.get_http_client().get("test"), "Value")
        httpretty.reset()

    def test_username_changed(self):
        self._perform_simple_request()  # use the existing credentials once

        self.wva.username = "bob"
        self.assertEqual(self.wva.username, "bob")

        self.prepare_json_response("GET", "/ws/testing/1/2/3", {"this": "is a test"})
        self.assertEqual(self.wva.get_http_client().get("testing/1/2/3"),
                         {"this": "is a test"})  # from previous test
        req = self._get_last_request()
        username, password = self._get_username_pass(req)
        self.assertEqual(username, six.b("bob"))
        self.assertEqual(password, six.b("pass"))

    def test_password_changed(self):
        self._perform_simple_request()
        self.wva.password = "DragonDove"
        self.assertEqual(self.wva.password, "DragonDove")

        self.prepare_json_response("GET", "/ws/testing/1/2/3", {"this": "is a test"})
        self.assertEqual(self.wva.get_http_client().get("testing/1/2/3"),
                         {"this": "is a test"})  # from previous test
        req = self._get_last_request()
        username, password = self._get_username_pass(req)
        self.assertEqual(username, six.b("user"))
        self.assertEqual(password, six.b("DragonDove"))

    def test_use_https_changed(self):
        self._perform_simple_request()
        self.wva.use_https = False
        self.assertEqual(self.wva.use_https, False)
        httpretty.register_uri("GET", "http://192.168.100.1/ws/123/4",
                               match_querystring=False, status=200, body="Testing HTTP")
        self.assertEqual(self.wva.get_http_client().get("123/4"), "Testing HTTP")

    def test_hostname_changed(self):
        self._perform_simple_request()
        httpretty.reset()

        self.wva.hostname = "my.new.host"
        self.assertEqual(self.wva.hostname, "my.new.host")

        httpretty.register_uri("GET", "https://my.new.host/ws/TESTING",
                               match_querystring=False, status=200, body="A response from my.new.host")
        self.assertEqual(self.wva.get_http_client().get("TESTING"), "A response from my.new.host")

    def test_json_get(self):
        self.prepare_json_response("GET", "/ws/testing/1/2/3", {
            "this": "is a test"
        })
        self.assertEqual(self.wva.get_http_client().get("testing/1/2/3"), {"this": "is a test"})

    def test_get(self):
        self.prepare_response("GET", "/ws/testing/1/2/3", "A RESPONSE")
        self.assertEqual(self.wva.get_http_client().get("testing/1/2/3"), "A RESPONSE")

    def test_json_post(self):
        self.prepare_json_response("POST", "/ws/post", {"error": "an error"})
        self.assertEqual(self.wva.get_http_client().post_json("post", {"my": "post request"}), {"error": "an error"})
        self.assertEqual(self._get_last_request().body, six.b('{"my": "post request"}'))

