# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.


class WVAError(Exception):
    """Base class for all WVA API Errors that may occur"""


class WVAHttpRequestError(WVAError):
    """We tried to make a web services call but could not even connect

    :type wrapped_exception: requests.exceptions.RequestException
    """

    def __init__(self, e):
        self.wrapped_exception = e
        WVAError.__init__(self, e)


class WVAHttpError(WVAError):
    """An error that occurs when making an HTTP Web Services API Call

    :type response: requests.Response
    """

    def __init__(self, response):
        WVAError.__init__(self, "Unexpected HTTP status {!r} {!r}".format(
            response.status_code, type(self).__name__))
        self.response = response


class WVAHttpBadRequestError(WVAHttpError):
    """A request was made but we received an HTTP status 400 "Bad Request"

    This failure case is returned under the following conditions:

    * The URI cannot be parsed; particularly if the URI is too long for the
      internal buffering of the web services engine.
    * The web services are unable to parse a document successfully based on the content type.
    * Failure attempting to set the time.
    * Failure parsing the fields of a record in a PUT operation (for example, the URI specified
      for an alarm not referencing something that supports alarms).
    """


class WVAHttpUnauthorizedError(WVAHttpError):
    """A request was made but we received an HTTP status 401 "Unauthorized"

    The request requires authentication. The client should repeat the request with HTTP
    basic authentication using the admin login and password.  If the request already
    included authentication, the login and password are incorrect.
    """


class WVAHttpForbiddenError(WVAHttpError):
    """A request was made but we received an HTTP status 403 "Forbidden"

    This failure case is returned under the following conditions:

    * The specified URI in the request URL is not one that can managed by the
      web services user due to permissions embedded within the system.

    This failure is most common when trying to manipulate files in the filesystem.
    """


class WVAHttpNotFoundError(WVAHttpError):
    """A request was made but  we received an HTTP status 404 "Not Found"

    This failure case is returned under the following conditions:

    * The specified URI in the request URL is not one recognized by the web services system.

    For alarms and subscriptions, a PUT can be made to a previously unknown URI to create an
    alarm or subscription, but a GET or DELETE of an as-yet unknown URI will generate this error
    condition.
    """


class WVAHttpMethodNotAllowedError(WVAHttpError):
    """A request was made but we received an HTTP status 405 "Not Allowed"

    This failure case is returned when the requested URI is recognized, but the HTTP method
    (for example, GET or PUT) in use is not supported in conjunction with that URI. Using
    the Index of Web Services Resources, you can quickly determine which methods are compatible
    with which URIs.
    """


class WVAHttpNotAcceptableError(WVAHttpError):
    """A request was made but we received an HTTP status 406 "Unacceptable"

    This failure case is returned when an HTTP method (for example, GET) requests a response,
    but the server is not able to deliver a document with that content type for the specified URI.
    This failure could happen if a request arrived with an "Accept: text/html" header, and the URI
    was XML or JSON only.
    """


class WVAHttpRequestTooLongError(WVAHttpError):
    """A request was made but we received an HTTP status 414 "Request-URI Too Long"

    This failure case is returned when the requested URI is longer than the web services
    system is able to parse.
    """


class WVAHttpUnsupportedMediaTypeError(WVAHttpError):
    """A request was made but we received an HTTP status 415 "Unsupported Media Type"

    This failure case is returned when an HTTP method (for example, PUT) supplies a document
    with a content type that is unexpected for the specified URI. This failure could happen
    if a document arrived with a "Content-type: text/html" header, and the URI was XML or JSON only.
    """


class WVAHttpInternalServerError(WVAHttpError):
    """A request was made but we received an HTTP status 500 "Internal Server Error"

    This failure case is returned when there are unexpected errors unrelated to the requests
    or responses themselves. Possible conditions resulting in this code include:

    * An unexpected failure registering an alarm.
    * An unexpected failure querying the vehicle bus subsystem.
    * An inability to read or write the internal resources associated with LEDs.
    """


class WVAHttpServiceUnavailableError(WVAHttpError):
    """A request was made but we received an HTTP status 503 "Service Unavailable"

    This failure case is returned when a data query could not be fully processed due to
    transient state in the web server. Possible conditions resulting in this code include:

    * A temporary lack of memory to allocate for parsing requests or generating
      responses can generate this response.
    * A vehicle bus data request is made to a URI known to potentially be available
      on the bus, but the specified data has not yet been received by the Digi device.
    """


HTTP_STATUS_EXCEPTION_MAP = {
    200: None,  # No exception, success!
    400: WVAHttpBadRequestError,
    401: WVAHttpUnauthorizedError,
    403: WVAHttpForbiddenError,
    404: WVAHttpNotFoundError,
    405: WVAHttpMethodNotAllowedError,
    414: WVAHttpNotAcceptableError,
    415: WVAHttpUnsupportedMediaTypeError,
    500: WVAHttpInternalServerError,
    503: WVAHttpServiceUnavailableError,
}
