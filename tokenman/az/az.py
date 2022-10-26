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

import os
import logging
from datetime import datetime
from datetime import timezone
from pathlib import Path
from tokenman.module import ModuleBase
from tokenman.state import RunState
from tokenman.az.azure_profile import AzureProfile
from tokenman.az.msal_token_cache import MSALTokenCache


class AZ(ModuleBase):
    """az command handler"""

    @classmethod
    def run(
        cls,
        state: RunState,
        client_id: str,
    ):
        """Run the 'az' command

        :param state: run state
        :param client_id: client id to exchange token for
        :param resource: token audience
        :param scope: token scope
        """
        # Ensure the .azure directory exists
        user_home = str(Path.home())

        # If the Azure CLI directory exists, back it up
        if Path(f"{user_home}/.azure").is_dir():
            logging.debug("Azure CLI directory exists, backing up: `.azure_backup`")
            utc_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            os.rename(f"{user_home}/.azure", f"{user_home}/.azure_backup.{utc_now}")

        Path(f"{user_home}/.azure").mkdir(parents=True, exist_ok=True)

        # Perform token exchange and generate MSAL Token Cache
        logging.info("Generating MSAL Token Cache")
        token_cache_created = MSALTokenCache.generate(state, client_id)

        if token_cache_created:
            logging.info("Generating Azure Profile")
            azure_profile = AzureProfile.generate(state)

            if azure_profile:
                logging.info("Successfully generated Azure CLI authentication files")
