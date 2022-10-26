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
from datetime import datetime
from datetime import timezone
from tokenman.module import ModuleBase
from tokenman.state import RunState
from typing import List


class Swap(ModuleBase):
    """Swap command handler"""

    @classmethod
    def run(
        cls,
        state: RunState,
        client_id: str,
        resource: str,
        scope: List[str],
    ):
        """Run the 'swap' command

        :param state: run state
        :param client_id: client id to exchange token for
        :param resource: token audience
        :param scope: token scope
        """
        if not state.token_cache.refresh_token:
            logging.error("No refresh token found to perform token exchange")
            return

        logging.info(f"Acquiring new token for: '{client_id}'")

        # Acquire a new token specific for Office
        new_token = cls.acquire_token(
            cls,
            refresh_token=state.token_cache.refresh_token,
            client_id=client_id,
            resource=resource,
            scope=scope,
            proxies=state.proxies,
        )

        # Handle invalid token
        if not new_token:
            logging.error("No access token retrieved")
            return

        state.token_cache.access_token = new_token["access_token"]
        state.token_cache.refresh_token = new_token["refresh_token"]

        # Get UPN from token if possible, fail over to 'token'
        upn = (
            state.token_cache.access_token_payload.get("unique_name", None)
            or state.token_cache.access_token_payload.get("upn", None)
            or "token"
        )

        utc_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = state.output / f"{upn}.{client_id}.{utc_now}.json"
        logging.info(f"\tOutput: {filename}")

        cls.write_json(
            cls,
            filename=filename,
            data=new_token,
        )

        # Only for the 'swap' command, output retrieved data, specifically the
        # new access token for ease of use
        logging.info(f'\tAccess Token:\n\n{new_token["access_token"]}')
