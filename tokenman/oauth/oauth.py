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
import webbrowser
from datetime import datetime
from datetime import timezone
from tokenman.module import ModuleBase
from tokenman.oauth.devicecode import DeviceCode
from tokenman.oauth.poll import Poll
from tokenman.oauth.poll import PollThread
from tokenman.state import RunState
from typing import List


class OAuth(ModuleBase):
    """oAuth device code flow handler"""

    @classmethod
    def run(
        cls,
        state: RunState,
        client_id: str,
        scope: List[str],
    ):
        """Run the 'oauth' command

        :param state: run state
        :param client_id: client id to exchange token for
        :param scope: token scope
        """
        default_scope = ["profile", "openid", "offline_access"]
        token_scope = list(set(scope + default_scope))  # dedup
        token_scope = "%20".join(token_scope)

        # Generate a device code token
        logging.info("Requesting new device code")
        device_code = DeviceCode.run(
            client_id=client_id,
            scope=token_scope,
            proxies=state.proxies,
        )

        # Handle invalid response
        if not device_code:
            logging.error("No device code retrieved")
            return

        # Begin polling MS for authentication in the background
        # via threading
        logging.info("Starting authentication poll in background")
        pt = PollThread(
            target=Poll.run,
            args=(
                device_code,
                client_id,
                token_scope,
                state.proxies,
            ),
        )
        pt.start()

        # Open a browser for the user to login
        logging.info("Launching browser for authentication")
        logging.info(f"Enter the following device code: {device_code['user_code']}")
        logging.info("Close the browser or tab once authentication has completed to continue")  # fmt: skip

        try:
            webbrowser.open(
                url="https://microsoft.com/devicelogin",
                new=0,
                autoraise=True,
            )
        except:
            logging.warn("Could not open browser")
            logging.warn("Browse to 'https://microsoft.com/devicelogin' to perform device code authentication")  # fmt: skip

        # Save tokens
        auth_token = pt.join()

        if auth_token:
            utc_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            filename = state.output / f"devicecode.token.{utc_now}.json"
            logging.info(f"\tOutput: {filename}")

            cls.write_json(
                cls,
                filename=filename,
                data=auth_token,
            )

        else:
            logging.error("Could not retrieve oAuth token")
