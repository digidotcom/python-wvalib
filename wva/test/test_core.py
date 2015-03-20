# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from wva import WVA
from wva.test.test_utilities import WVATestBase


class TestWVA(WVATestBase):
    def test_construction(self):
        wva = WVA("host", "bob", "secrets")
        self.assertEqual(wva.hostname, "host")
        self.assertEqual(wva.username, "bob")
        self.assertEqual(wva.password, "secrets")
        self.assertEqual(wva.use_https, True)
