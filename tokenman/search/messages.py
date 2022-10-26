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
from tokenman import utils
from tokenman.module import ModuleBase
from tokenman.state import RunState
from typing import Any
from typing import List
from typing import Dict


class Messages(ModuleBase):
    """Messages search class"""

    def _search(
        self,
        access_token: str,
        keywords: List[str] = utils.SEARCH_KEYWORDS,
        proxies: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Search messages files via Graph API accessible by the given user
        https://docs.microsoft.com/en-us/graph/search-concept-files

        :param access_token: access token
        :param keywords: list of keywords to search
        :param proxies: http request proxy
        :returns: search results
        """
        search = " OR ".join(keywords)  # KQL logical OR
        return self.msgraph_search(
            self,
            entity_types=["message"],
            search=search,
            access_token=access_token,
            proxies=proxies,
        )

    @classmethod
    def search(
        cls,
        state: RunState,
        keywords: List[str] = utils.SEARCH_KEYWORDS,
    ):
        """Search messages files via Graph API

        :param state: run state
        :param search: search term
        """
        # Check if we have an access token for Office
        if not cls.check_token(
            cls,
            state.token_cache.access_token_payload,
            "Microsoft Office",
        ):
            if not state.token_cache.refresh_token:
                logging.error("No refresh token found to perform token exchange")
                return

            logging.debug(f"Acquiring new token for: 'Microsoft Office'")

            # Acquire a new token specific for Office
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

        logging.info(f"Searching 'messages' for: {keywords}")

        # Search content for keywords
        results = cls._search(
            cls,
            access_token=state.token_cache.access_token,
            keywords=keywords,
            proxies=state.proxies,
        )
        total_results = len(results["value"])
        logging.info(f"\tSearch Results: {total_results}")

        # If search results found, write to output file
        if total_results > 0:
            utc_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            filename = state.output / f"search.messages.{utc_now}.json"
            logging.info(f"\tOutput: {filename}")

            cls.write_json(
                cls,
                filename=filename,
                data=results,
            )
