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

import logging
import requests  # type: ignore
import urllib
from typing import Any
from typing import Dict


class DeviceCode:
    """Device code flow handler"""

    @classmethod
    def run(
        cls,
        client_id: str,
        scope: str,
        proxies: Dict[str, str] = None,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """Generate a device code for oAuth device code flow

        :param client_id: client id to request token for
        :param scope: token scope
        :param proxies: http request proxy
        :param verify: http request certificate verification
        :returns: device code json response
        """
        if proxies:
            verify = False

        # Build device code request
        url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/devicecode"
        params = (("client_id", client_id), ("scope", scope))
        data = urllib.parse.urlencode(params)

        # Request a new device code from Microsoft for the given client ID
        try:
            response = requests.post(
                url,
                data=data,
                proxies=proxies,
                verify=verify,
            )

            if response.status_code != 200:
                logging.error(f"Invalid device code response:\n{response.json()}")
                return None

            device_code = response.json()

            logging.debug(f"Device code response: {device_code}")

        except Exception as e:
            logging.error(f"Failed to request device code from Microsoft: {e}")
            return None

        return device_code
