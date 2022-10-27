# Copyright 2022 Secureworks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import requests  # type: ignore
import threading
import time
import urllib
from typing import Any
from typing import Dict


class Poll:
    """Device code authentication polling handler

    Based on:
    https://github.com/secureworks/squarephish/blob/main/squarephish/modules/server/auth.py
    """

    @classmethod
    def run(
        cls,
        device_code: Dict[str, Any],
        client_id: str,
        scope: str,
        proxies: Dict[str, str] = None,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """Poll the MS token endpoint for valid authentication

        :param device_code: device code json response
        :param client_id: client id requested for the token
        :param scope: requested token scope
        :param proxies: http request proxy
        :param verify: http request certificate verification
        :returns: token json response
        """
        if proxies:
            verify = False

        # Generate POST request data for polling Microsoft for authentication
        url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
        params = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:device_code"),
            ("code", device_code["device_code"]),
            ("client_id", client_id),
            ("scope", scope),
        )
        data = urllib.parse.urlencode(params)

        # Poll only for the time given before the device code expires
        expires_in = int(device_code["expires_in"]) / 60
        end_delta = datetime.timedelta(minutes=expires_in)
        stop_time = datetime.datetime.now() + end_delta

        while True:
            logging.debug(f"Polling for oAuth authentication")
            response = requests.post(
                url,
                data=data,
                proxies=proxies,
                verify=verify,
            )

            # Successful auth
            if response.status_code == 200:
                break

            # Bad response
            if response.json()["error"] != "authorization_pending":
                logging.error(f"Invalid poll response:\n{response.json()}")
                return None

            # Handle device code expiration/timeout
            if datetime.datetime.now() >= stop_time:
                logging.error(f"Device code expired")
                return None

            # Wait the provided interval time between polls
            time.sleep(int(device_code["interval"]))

        # Grab the token response
        token_response = response.json()
        return token_response


class PollThread(threading.Thread):
    """Custom threading class to poll for device code authentication"""

    def __init__(
        self,
        group=None,
        target=None,
        name=None,
        args=(),
        kwargs={},
        Verbose=None,
    ):
        """Initialize polling thread"""
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def join(self, *args):
        """Override join to return value"""
        threading.Thread.join(self, *args)
        return self._return

    def run(self):
        """Override run to return value"""
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
