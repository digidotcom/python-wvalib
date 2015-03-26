# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json
import requests
from requests.packages import urllib3
import six
import warnings
from wva.exceptions import WVAHttpRequestError, HTTP_STATUS_EXCEPTION_MAP, WVAHttpError


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

    def _get_ws_url(self, uri):
        base = "https" if self._use_https else "http"
        uri = uri.lstrip("/")  # remove leading slash if present
        return "{base}://{hostname}/ws/{relpath}".format(
            base=base,
            hostname=self._hostname,
            relpath=uri
        )

    def raw_request(self, method, uri, **kwargs):
        """Perform a WVA web services request and return the raw response object

        :param method: The HTTP method to use when making this request
        :param uri: The path past /ws to request.  That is, the path requested for
            a relpath of `a/b/c` would be `/ws/a/b/c`.
        :raises WVAHttpSocketError: if there was an error making the HTTP request.  That is,
            the request was unable to make it to the WVA for some reason.
        """
        with warnings.catch_warnings():  # catch warning about certs not being verified
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
            warnings.simplefilter("ignore", urllib3.exceptions.InsecurePlatformWarning)
            try:
                response = self._get_session().request(method, self._get_ws_url(uri), **kwargs)
            except requests.RequestException as e:
                # e.g. raise new_exc from old_exc
                six.raise_from(WVAHttpRequestError(e), e)
            else:
                return response

    def request(self, method, uri, **kwargs):
        """Perform a WVA web services request and return the decoded value if successful

        :param method: The HTTP method to use when making this request
        :param uri: The path past /ws to request.  That is, the path requested for
            a relpath of `a/b/c` would be `/ws/a/b/c`.
        :raises WVAHttpError: if a response is received but the success is non-success
        :raises WVAHttpSocketError: if there was an error making the HTTP request.  That is,
            the request was unable to make it to the WVA for some reason.
        :return: If the response content type is JSON, it will be deserialized and a
            python dictionary containing the information from the json document will
            be returned.  If not a JSON response, a unicode string of the response
            text will be returned.
        """
        response = self.raw_request(method, uri, **kwargs)
        if response.status_code != 200:
            exception_class = HTTP_STATUS_EXCEPTION_MAP.get(response.status_code, WVAHttpError)
            raise exception_class(response)

        if response.headers.get("content-type") == "application/json":
            return json.loads(response.text)
        else:
            return response.text

    def delete(self, uri, **kwargs):
        """DELETE the specified web service path

        See :meth:`request` for additional details.
        """
        return self.request("DELETE", uri, **kwargs)

    def get(self, uri, **kwargs):
        """GET the specified web service path and return the decoded response contents

        See :meth:`request` for additional details.
        """
        return self.request("GET", uri, **kwargs)

    def post(self, uri, data, **kwargs):
        """POST the provided data to the specified path

        See :meth:`request` for additional details.  The `data` parameter here is
        expected to be a string type.
        """
        return self.request("POST", uri, data=data, **kwargs)

    def post_json(self, uri, data, **kwargs):
        """POST the provided data as json to the specified path

        See :meth:`request` for additional details.
        """
        encoded_data = json.dumps(data)
        kwargs.setdefault("headers", {}).update({
            "Content-Type": "application/json",  # tell server we are sending json
        })
        return self.post(uri, data=encoded_data, **kwargs)

    def put(self, uri, data, **kwargs):
        """PUT the provided data to the specified path

        See :meth:`request` for additional details.  The `data` parameter here is
        expected to be a string type.
        """
        return self.request("PUT", uri, data=data, **kwargs)

    def put_json(self, uri, data, **kwargs):
        """PUT the provided data as json to the specified path

        See :meth:`request` for additional details.
        """
        encoded_data = json.dumps(data)
        kwargs.setdefault("headers", {}).update({
            "Content-Type": "application/json",  # tell server we are sending json
        })
        return self.put(uri, data=encoded_data, **kwargs)
