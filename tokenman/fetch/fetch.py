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

from tokenman.fetch.applications import Applications
from tokenman.fetch.drives import Drives
from tokenman.fetch.emails import Emails
from tokenman.fetch.groups import Groups
from tokenman.fetch.organizations import Organizations
from tokenman.fetch.serviceprincipals import ServicePrincipals
from tokenman.fetch.users import Users
from tokenman.state import RunState
from typing import List


class Fetch:
    """Fetch command handler"""

    @classmethod
    def run(
        cls,
        state: RunState,
        modules: List[str],
    ):
        """Run the 'fetch' command

        :param state: run state
        :param modules: fetch modules to run
        """
        # Run each module based on the provided flag data from the user
        if any(m in modules for m in ["users", "all"]):
            Users.fetch(state)

        if any(m in modules for m in ["groups", "all"]):
            Groups.fetch(state)

        if any(m in modules for m in ["organizations", "all"]):
            Organizations.fetch(state)

        if any(m in modules for m in ["emails", "all"]):
            Emails.fetch(state)

        if any(m in modules for m in ["applications", "all"]):
            Applications.fetch(state)

        if any(m in modules for m in ["serviceprincipals", "all"]):
            ServicePrincipals.fetch(state)

        if any(m in modules for m in ["drives", "all"]):
            Drives.fetch(state)
