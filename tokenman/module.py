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
from typing import Any
from typing import List
from typing import Dict
from tokenman import utils
from tokenman import acquire


class ModuleBase:
    """Module base class for shared functions"""

    def write_json(
        self,
        filename: str,
        data: Dict[str, str],
    ):
        """Write a data structure as JSON to disk

        :param filename: full name of output file
        :param data: data structure to write to system
        """
        try:
            with open(filename, "w") as f:
                json.dump(data, f)

        except Exception as e:
            logging.error(f"Failed to write JSON: {e}")
            # Fall back to printing data raw in case the file
            # couldn't write to disk
            print(json.dumps(data, indent=4))

    def check_token(
        self,
        access_token_payload: Dict[str, Any],
        client_id: str,
        resource: str = "https://graph.microsoft.com",
    ) -> bool:
        """Check an access token for a given client id
        or resource.

        :param access_token_payload: access token object
        :param client_id: client id or name associated to foci map
        :param resource: token resource/audience
        :returns: if a token is valid for given client/audience
        """
        # Check if there is an access token
        if not access_token_payload:
            return False

        # Check if the token is targeting the correct application
        try:
            if access_token_payload["appid"] == client_id or (
                client_id in utils.FOCI_CLIENT_IDS.keys()
                and access_token_payload["appid"] == utils.FOCI_CLIENT_IDS[client_id]
            ):
                return True
        except:
            pass

        # Check if the token is targeting the correct audience/scope
        try:
            if (
                access_token_payload["aud"] == resource
                or resource in access_token_payload["scp"]
            ):
                return True
        except:
            pass

        return False

    def acquire_token(
        self,
        refresh_token: str,
        client_id: str = None,
        client_name: str = None,
        resource: str = None,
        scope: List[str] = [".default"],
        proxies: Dict[str, str] = None,
        verify: bool = True,
    ) -> Dict[str, Any]:
        """Retrieve a new token for the specified application/resource

        :param refresh_token: refresh token
        :param client_id: target application client id
        :param client_name: target application client name
        :param resource: target token resource/audience
        :param scopes: target token scopes
        :param proxies: http request proxy
        :param verify: http request certificate verification
        :returns: new token object
        """
        # Require a client id or name
        if not client_id and not client_name:
            logging.error("Missing required client id or name")
            return None

        # Validate client name in foci map
        try:
            if client_name and not client_id:
                client_id = utils.FOCI_CLIENT_IDS[client_name]

        except KeyError:
            logging.error("Invalid client name provided")
            return None

        new_refresh_token = acquire.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            client_id=client_id,
            resource=resource,
            scope=scope,
            proxies=proxies,
            verify=verify,
        )

        return new_refresh_token

    def msgraph_fetch(
        self,
        path: str,
        access_token=str,
        proxies: Dict[str, str] = None,
        verify: bool = True,
        limit: int = 100,
    ) -> Dict[str, str]:
        """Fetch data via Microsoft Graph

        :param path: graph api path
        :param access_token: access token
        :param proxies: http request proxy
        :param verify: http request certificate verification
        :param limit: max number of pages to fetch
        """
        if proxies:
            verify = False

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"https://graph.microsoft.com/v1.0/{path}"

        # Rebuild the search response JSON scheme
        # Exclude @odata.nextLink - only use this to get the next page
        results = {"@odata.context": None, "value": []}

        count = 0
        try:
            # Continue to loop while there is more data/until we hit
            # our request limit
            while url and count <= limit:
                count += 1
                response = requests.get(
                    url=url,
                    headers=headers,
                    proxies=proxies,
                    verify=verify,
                )
                json_response = response.json()

                # Handle errors
                if "error" in json_response:
                    logging.error(f'Error: {json_response["error"]["message"]}')
                    break

                # Get the context (only on first request)
                if not results["@odata.context"]:
                    results["@odata.context"] = json_response.get("@odata.context", None)  # fmt: skip

                # Get the values returned and append to results
                value = json_response.get("value", None)
                if value:
                    results["value"] += value

                # Get the next URL if more results
                url = json_response.get("@odata.nextLink", None)

            return results

        except requests.RequestException as e:
            logging.error(f"Graph Fetch Error: {e}")
            return results

    def msgraph_search(
        self,
        entity_types: List[str],
        search: str,
        access_token=str,
        proxies: Dict[str, str] = None,
        verify: bool = True,
    ) -> Dict[str, str]:
        """Search data via Microsoft Graph Search

        :param entity_types: entity(ies) to search
        :param search: search term
        :param access_token: access token
        :param proxies: http request proxy
        :param verify: http request certificate verification
        """
        if proxies:
            verify = False

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        json = {
            "requests": [
                {
                    "entityTypes": entity_types,
                    "query": {
                        "queryString": search,
                    },
                }
            ]
        }

        try:
            response = requests.post(
                url=f"https://graph.microsoft.com/v1.0/search/query",
                json=json,
                headers=headers,
                proxies=proxies,
                verify=verify,
            )
            json_response = response.json()

            # Handle errors
            if "error" in json_response:
                logging.error(f'Error: {json_response["error"]["message"]}')
                return None

            return json_response

        except requests.RequestException as e:
            logging.error(f"Graph Search Error: {e}")
            return None
