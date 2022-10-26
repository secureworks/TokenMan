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
from typing import Any
from typing import Dict


class Drives(ModuleBase):
    """OneDrive drives retrieval class"""

    def _fetch_drives(
        self,
        access_token: str,
        proxies: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Retrieve all drives for the given user

        :param access_token: access token
        :param proxies: http request proxy
        """
        return self.msgraph_fetch(
            self,
            path="me/drives",
            access_token=access_token,
            proxies=proxies,
        )

    @classmethod
    def fetch(cls, state: RunState):
        """Fetch user drives

        :param state: run state
        """
        # Check if we have an access token for MS Office
        if not cls.check_token(
            cls,
            state.token_cache.access_token_payload,
            "Microsoft Office",
        ):
            if not state.token_cache.refresh_token:
                logging.error("No refresh token found to perform token exchange")
                return

            logging.debug("Acquiring new token for: 'Microsoft Office'")

            # Acquire a new token specific for Microsoft Office
            new_token = cls.acquire_token(
                cls,
                refresh_token=state.token_cache.refresh_token,
                client_name="Microsoft Office",
                proxies=state.proxies,
            )

            # Handle invalid token
            if not new_token:
                logging.error("Could not exchange for new token")
                return

            # Update state access token
            state.token_cache.access_token = new_token["access_token"]
            state.token_cache.refresh_token = new_token["refresh_token"]

        logging.info("Fetching drives")

        # Fetch drives
        drives = cls._fetch_drives(
            cls,
            access_token=state.token_cache.access_token,
            proxies=state.proxies,
        )
        drives_count = len(drives["value"])
        logging.info(f"\tDrives: {drives_count}")

        # If drives found, write to disk
        if drives_count > 0:
            utc_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            filename = state.output / f"fetch.drives.{utc_now}.json"
            logging.info(f"\tOutput: {filename}")

            cls.write_json(
                cls,
                filename=filename,
                data=drives,
            )
