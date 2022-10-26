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
from typing import List
from typing import Dict


def acquire_token_by_refresh_token(
    refresh_token: str,
    client_id: str,
    resource: str = None,
    scope: List[str] = [".default"],
    proxies: Dict[str, str] = None,
    verify: bool = True,
    *args,
    **kwargs,
) -> Dict[str, str]:
    """Acquire a new refresh token using by querying the 'oauth2/token'
    endpoint. Manually exchange instead of using MSAL to provide slightly
    more granularity in token options via 'resource' parameter.

    :param refresh_token: refresh token
    :param client_id: target client id
    :param resource: target resource/audience
    :param scopes: target scopes
    :param proxies: http request proxy
    :param verify: http request certificate verification
    :returns: token object
    """
    endpoint = "https://login.microsoftonline.com/common/oauth2/token"

    # If HTTP proxy provided, default to no ssl validation
    if proxies:
        verify = False

    # Build scope
    default_scope = ["profile", "openid", "offline_access"]
    token_scope = list(set(scope + default_scope))  # dedup
    token_scope = "%20".join(token_scope)

    # Build token POST request data
    data = f"client_id={client_id}"
    data += "&grant_type=refresh_token"
    data += "&client_info=1"
    data += f"&refresh_token={refresh_token}"
    data += f"&scope={token_scope}"

    if resource:
        data += f"&resource={resource}"

    # Request token
    try:
        response = requests.post(
            endpoint,
            data=data,
            proxies=proxies,
            verify=verify,
        )
        token = response.json()

        # Handle errors
        if "error" in token.keys():
            raise Exception(token["error_description"])

        return token

    except Exception as e:
        logging.error(f"Failed to acquire token: {e}")
        return None
