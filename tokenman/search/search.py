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

from tokenman import utils
from tokenman.search.messages import Messages
from tokenman.search.onedrive import OneDrive
from tokenman.search.sharepoint import SharePoint
from tokenman.state import RunState
from typing import List


class Search:
    """Search command handler"""

    @classmethod
    def run(
        cls,
        state: RunState,
        modules: List[str],
        keywords: List[str] = utils.SEARCH_KEYWORDS,
    ):
        """Run the 'search' command

        :param state: run state
        :param modules: search modules to run
        :param keywords: keywords to search for
        """
        # Run each module based on the provided flag data from the user
        if any(m in modules for m in ["messages"]):
            Messages.search(state=state, keywords=keywords)

        if any(m in modules for m in ["onedrive"]):
            OneDrive.search(state=state, keywords=keywords)

        # Perform this last in case 'all' modules are run, as this module
        # requires a different access token
        if any(m in modules for m in ["sharepoint"]):
            SharePoint.search(state=state, keywords=keywords)
