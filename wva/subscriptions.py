# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.


class WVASubscription(object):
    """Provide access to a subscription on the WVA"""

    def __init__(self, http_client, short_name):
        self._http_client = http_client
        self.short_name = short_name

    def create(self, uri, buffer="queue", interval=10):
        """Create a subscription with this short name and the provided parameters

        For more information on what the parameters required here mean, please
        refer to the `WVA Documentation <http://goo.gl/DRcOQf>`_.

        :raises WVAError: If there is a problem creating the new subscription
        """
        return self._http_client.put_json("subscriptions/{}".format(self.short_name), {
            "subscription": {
                "uri": uri,
                "buffer": buffer,
                "interval": interval,
            }
        })

    def delete(self):
        """Delete this subscription

        :raises WVAError: If there is a problem deleting the subscription
        """
        return self._http_client.delete("subscriptions/{}".format(self.short_name))

    def get_metadata(self):
        """Get the metadata that is available for this subscription

        The metadata for a subscription is a dictionary like the following.  Details
        on the elements may be found in the `WVA documentation <http://goo.gl/DRcOQf>`_::

            {
                'buffer': 'queue',
                'interval': 10,
                'uri': 'vehicle/data/TripDistance'
            }

        :raises WVAError: if there is a problem querying the WVA for the metadata
        :returns: A dictionary containing the metadata for this subscription
        """
        return self._http_client.get("subscriptions/{}".format(self.short_name))["subscription"]
