# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json
import requests
from requests.packages import urllib3
import warnings


class WVAHttpClient(object):
    """Wrapper around requests for making WVA Web Service Calls"""

    def __init__(self, hostname, username, password, use_https=True):
        self._hostname = hostname
        self._username = username
        self._password = password
        self._use_https = use_https
        self._session = None

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, hostname):
        self._hostname = hostname
        self._session = None  # invalidate the current session

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        self._username = username
        self._session = None  # invalidate the current session

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password
        self._session = None  # invalidate the current session

    @property
    def use_https(self):
        return self._use_https

    @use_https.setter
    def use_https(self, use_https):
        self._use_https = use_https
        self._session = None

    def _get_session(self):
        if self._session is None:
            self._session = requests.Session()
            self._session.auth = (self._username, self._password)
            self._session.verify = False  # self-signed certificate
            self._session.headers.update({
                'Accept': 'application/json',
            })
        return self._session

    def _get_ws_url(self, relpath):
        base = "https" if self._use_https else "http"
        return "{base}://{hostname}/ws/{relpath}".format(
            base=base,
            hostname=self._hostname,
            relpath=relpath
        )

    def _request(self, method, relpath, **kwargs):
        with warnings.catch_warnings():  # catch warning about certs not being verified
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
            warnings.simplefilter("ignore", urllib3.exceptions.InsecurePlatformWarning)
            response = self._get_session().request(method, self._get_ws_url(relpath), **kwargs)
            if response.headers.get("content-type") == "application/json":
                return json.loads(response.text)
            else:
                return response.text

    def get(self, relpath, **kwargs):
        return self._request("GET", relpath, **kwargs)

    def post_json(self, relpath, data, **kwargs):
        encoded_data = json.dumps(data)
        return self._request("POST", relpath, data=encoded_data, **kwargs)

    def put_json(self, relpath, data, **kwargs):
        encoded_data = json.dumps(data)
        return self._request("PUT", relpath, data=encoded_data, **kwargs)

    def delete(self, relpath, **kwargs):
        return self._request("DELETE", relpath, **kwargs)


class WVA(object):

    def __init__(self, hostname, username, password, use_https=True):
        self._client = WVAHttpClient(hostname, username, password, use_https)

    @property
    def hostname(self):
        return self._client.hostname

    @hostname.setter
    def hostname(self, hostname):
        self._client._hostname = hostname

    @property
    def username(self):
        return self._client.username

    @username.setter
    def username(self, username):
        self._client.username = username

    @property
    def password(self):
        return self._client.password

    @password.setter
    def password(self, password):
        self._client.password = password

    @property
    def use_https(self):
        return self._client.use_https

    @use_https.setter
    def use_https(self, use_https):
        self._client.use_https = use_https

    def get(self, relpath, **kwargs):
        return self._client.get(relpath, **kwargs)

    def post(self, relpath, data, **kwargs):
        return self._client.post_json(relpath, data, **kwargs)

    def put(self, relpath, data, **kwargs):
        return self._client.put_json(relpath, data, **kwargs)

    def delete(self, relpath, **kwargs):
        return self._client.delete(relpath, **kwargs)

    def get_all_config(self):
        config = {}
        for path in self._client.get("config")["config"]:
            if "factory_default" in path:
                continue  # this one doesn't work
            data = self._client.get(path)
            config[path.split("/")[1]] = data
        return config
