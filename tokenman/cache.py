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
from tokenman import utils
from typing import Any
from typing import Dict


class TokenCache:
    """Token cache management"""

    def __init__(
        self,
        access_token: str = None,
        refresh_token: str = None,
        id_token: str = None,
        client_info: str = None,
    ):
        """Token cache initialization

        :param access_token: access token string
        :param refresh_token: refresh token string
        :param id_token: id token string
        :param client_info: client info string
        """
        # Init and set data via properties
        self._access_token = None
        self._access_token_payload = None
        self.access_token = access_token

        self._id_token = None
        self.id_token_payload = None
        self.id_token = id_token

        self._client_info = None
        self._client_info_payload = None
        self.client_info = client_info

        # Set refresh token
        self.refresh_token = refresh_token

    @property
    def access_token(self):
        """Access token getter"""
        return self._access_token

    @access_token.setter
    def access_token(self, value: str):
        """Access token setter"""
        self._access_token = value
        if self._access_token:
            try:
                # Invoke access token payload setter
                self.access_token_payload = utils.decode_jwt(self._access_token)

            except Exception as e:
                logging.error(f"Failed to parse access token: {e}")

    @property
    def access_token_payload(self):
        """Access token payload getter"""
        return self._access_token_payload

    @access_token_payload.setter
    def access_token_payload(self, value: Dict[str, Any]):
        """Access token payload setter"""
        self._access_token_payload = value

    @property
    def id_token(self):
        """ID token getter"""
        return self._id_token

    @id_token.setter
    def id_token(self, value: str):
        """ID token setter"""
        self._id_token = value
        if self._id_token:
            try:
                # Invoke id token payload setter
                self.id_token_payload = utils.decode_jwt(self._id_token)

            except Exception as e:
                logging.error(f"Failed to parse id token: {e}")

    @property
    def id_token_payload(self):
        """ID token payload getter"""
        return self._id_token_payload

    @id_token_payload.setter
    def id_token_payload(self, value: Dict[str, Any]):
        """ID token payload setter"""
        self._id_token_payload = value

    @property
    def client_info(self):
        """Client info getter"""
        return self._client_info

    @client_info.setter
    def client_info(self, value: str):
        """Client info setter"""
        self._client_info = value

        # Base64 decode to JSON object
        if self._client_info:
            try:
                client_info = utils.pad_base64(self._client_info)
                client_info = utils.base64_to_json(client_info)
                self.client_info_payload = client_info

            except Exception as e:
                logging.error(f"Failed to parse client info: {e}")

    @property
    def client_info_payload(self):
        """Client info payload getter"""
        return self._client_info_payload

    @client_info_payload.setter
    def client_info_payload(self, value: Dict[str, Any]):
        """Client info payload setter"""
        self._client_info_payload = value
