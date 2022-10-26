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
from pathlib import Path
from tokenman.module import ModuleBase
from tokenman.state import RunState


class MSALTokenCache(ModuleBase):
    """Build MSAL Token Cache"""

    @classmethod
    def generate(
        cls,
        state: RunState,
        client_id: str = "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    ) -> bool:
        """Using a refresh token, exchange for an Azure CLI token and create
        an MSAL Token Cache file for Azure CLI

        :param state: run state
        :param client_id: client id to exchange for
        :returns: if token cache created
        """
        # Acquire a new token specific for Azure Management
        new_token = cls.acquire_token(
            cls,
            refresh_token=state.token_cache.refresh_token,
            client_id=client_id,
            resource="https://management.core.windows.net",
            proxies=state.proxies,
        )

        # Handle invalid token
        if not new_token:
            logging.error("No access token retrieved")
            return False

        try:
            logging.debug("Parsing Azure CLI token")

            # Update token cache
            state.token_cache.access_token = new_token["access_token"]
            state.token_cache.refresh_token = new_token["refresh_token"]
            state.token_cache.id_token = new_token["id_token"]
            state.token_cache.client_info = new_token["client_info"]

            # Parse data from token cache
            ## Exctract necessary data from the client info
            uid = state.token_cache.client_info_payload["uid"]

            ## AAD returns "preferred_username", ADFS returns "upn"
            upn = (
                state.token_cache.id_token_payload.get("preferred_username")
                or state.token_cache.id_token_payload["upn"]
            )
            tid = state.token_cache.id_token_payload["tid"]

            ## Exctract necessary data from the access token
            scope = state.token_cache.access_token_payload["scp"]
            client_id = state.token_cache.access_token_payload["appid"]
            expires_on = state.token_cache.access_token_payload["exp"] - 1
            cached_at = state.token_cache.access_token_payload["nbf"] + 10

        except Exception as e:
            logging.error(f"Token Parsing Exception: {e}")
            return False

        # Build MSAL Token Cache data structure
        # NOTE: This always assumes the authenticating token is for a user instead of
        #       a service principal
        msal_token_cache = {
            "AccessToken": {
                f"{uid}.{tid}-login.microsoftonline.com-accesstoken-{client_id}-{tid}-{scope}": {
                    "credential_type": "AccessToken",
                    "secret": state.token_cache.access_token,
                    "home_account_id": f"{uid}.{tid}",
                    "environment": "login.microsoftonline.com",
                    "client_id": client_id,
                    "target": scope,
                    "realm": tid,
                    "token_type": "Bearer",
                    "cached_at": cached_at,
                    "expires_on": expires_on,
                    "extended_expires_on": expires_on,
                }
            },
            "AppMetadata": {
                f"appmetadata-login.microsoftonline.com-{client_id}": {
                    "client_id": client_id,
                    "environment": "login.microsoftonline.com",
                    "family_id": "1",
                }
            },
            "RefreshToken": {
                f"{uid}.{tid}-login.microsoftonline.com-refreshtoken-{client_id}--{scope}": {
                    "credential_type": "RefreshToken",
                    "secret": state.token_cache.refresh_token,
                    "home_account_id": f"{uid}.{tid}",
                    "environment": "login.microsoftonline.com",
                    "client_id": client_id,
                    "target": scope,
                    "last_modification_time": cached_at,
                    "family_id": "1",
                }
            },
            "IdToken": {
                f"{uid}.{tid}-login.microsoftonline.com-idtoken-{client_id}-organizations-": {
                    "credential_type": "IdToken",
                    "secret": state.token_cache.id_token,
                    "home_account_id": f"{uid}.{tid}",
                    "environment": "login.microsoftonline.com",
                    "realm": "organizations",
                    "client_id": client_id,
                }
            },
            "Account": {
                f"{uid}.{tid}-login.microsoftonline.com-organizations": {
                    "home_account_id": f"{uid}.{tid}",
                    "environment": "login.microsoftonline.com",
                    "realm": "organizations",
                    "local_account_id": uid,
                    "username": upn,
                    "authority_type": "MSSTS",
                }
            },
        }

        # Write the token cache
        logging.info("\tWriting MSAL Token Cache to disk")
        with open(f"{str(Path.home())}/.azure/msal_token_cache.json", "w") as f:
            json.dump(msal_token_cache, f, indent=4)

        return True
