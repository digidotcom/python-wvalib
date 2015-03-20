# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
from wva.http_client import WVAHttpClient


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

    def get_all_config(self):
        config = {}
        for path in self._http_client.get("config")["config"]:
            if "factory_default" in path:
                continue  # this one doesn't work
            data = self._http_client.get(path)
            config[path.split("/")[1]] = data
        return config
