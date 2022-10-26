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

import json
import logging
import requests  # type: ignore
from pathlib import Path
from tokenman.module import ModuleBase
from tokenman.state import RunState
from typing import Any
from typing import Dict


class AzureProfile(ModuleBase):
    """Build Azure Profile"""

    def _get_subscriptions(
        self,
        access_token: str,
        proxies: Dict[str, str] = None,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """Retrieve all subscriptions the user has access to via
        Azure Management API

        :param refresh_token: user access token
        :param proxies: http request proxy
        :param verify: http request certificate verification
        :returns: subscription response
        """
        if proxies:
            verify = False

        endpoint = "https://management.azure.com/subscriptions?api-version=2019-11-01"

        # Default HTTP headers to replicate a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "Authorization": f"Bearer {access_token}",
        }

        try:
            logging.debug("Requesting accessible subscriptions")

            response = requests.get(
                endpoint,
                headers=headers,
                proxies=proxies,
                verify=verify,
            )
            r_json = response.json()

            # Handle errors
            if "error" in r_json.keys():
                raise Exception(r_json["message"])

            return r_json

        except Exception as e:
            logging.error(f"Subscriptions Request Exception: {e}")
            return None

    @classmethod
    def generate(
        cls,
        state: RunState,
    ) -> bool:
        """Using an Azure CLI access token, retrieve all accessible subscriptions

        :param state: run state
        :returns: boolean if profile file created
        """
        # Parse UPN from access token
        ## AAD returns "preferred_username", ADFS returns "upn"
        upn = (
            state.token_cache.id_token_payload.get("preferred_username")
            or state.token_cache.id_token_payload["upn"]
        )

        # Retrieve subscription list
        subscription_data = cls._get_subscriptions(
            cls, state.token_cache.access_token, state.proxies
        )
        if not subscription_data:
            logging.error("Failed to retrieve Azure subscription list")
            return False

        logging.debug(f'{subscription_data["count"]["value"]} subscriptions found')

        try:
            # Init azure profile data structure
            azure_profile = {"subscriptions": []}

            # When building the profile data structure, default the first
            # subscription and mark the rest as False
            default = True

            # Account for not subscriptions access
            if not subscription_data["value"]:
                logging.warning("User does not have access to any subscriptions")
                logging.warning("az cli will not recognize authentication as a result")

            # Loop over subscriptions and add to profile data structure
            for subscription in subscription_data["value"]:
                # NOTE: This always assumes the authenticating token is for a user instead of
                #       a service principal
                subscription_profile = {
                    "id": subscription["subscriptionId"],
                    "name": subscription["displayName"],
                    "state": subscription["state"],
                    "user": {
                        "name": upn,
                        "type": "user",
                    },
                    "isDefault": default,
                    "tenantId": subscription["tenantId"],
                    "environmentName": "AzureCloud",
                    "homeTenantId": subscription["tenantId"],
                    "managedByTenants": [],
                }

                if subscription["managedByTenants"]:
                    subscription_profile["managedByTenants"] = [
                        {"tenantId": t["tenantId"]}
                        for t in subscription["managedByTenants"]
                    ]

                azure_profile["subscriptions"].append(subscription_profile)

                if default:
                    logging.debug(f"Default subscription: '{subscription['displayName']}'")  # fmt: skip
                    default = False

        except Exception as e:
            logging.error(f"Azure Profile Exception: {e}")
            return False

        # Write the azure profile
        logging.info("\tWriting Azure Profile to disk")
        with open(f"{str(Path.home())}/.azure/azureProfile.json", "w") as f:
            json.dump(azure_profile, f, indent=4)

        return True
