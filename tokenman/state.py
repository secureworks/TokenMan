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

from pathlib import Path
from tokenman.cache import TokenCache


class RunState:
    """Run state management"""

    def __init__(
        self,
        token_cache: TokenCache,
        output: Path,
        proxy: str = None,
    ):
        """Initialize run state

        Maintain a state of the current AAD token cache,
        as well as proxy and output settings for the run.

        :param token_cache: token cache
        :param output: output directory object
        :param proxy: http proxy url
        """
        self.token_cache = token_cache
        self.output = output

        self.proxies = None
        if proxy:
            self.proxies = {"http": proxy, "https": proxy}
