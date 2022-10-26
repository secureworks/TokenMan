#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import urllib3  # type: ignore
from pathlib import Path
from tokenman import __title__
from tokenman import __version__
from tokenman import utils
from tokenman.args import parse_args
from tokenman.cache import TokenCache
from tokenman.state import RunState

# Command handlers
from tokenman.az import AZ
from tokenman.fetch import Fetch
from tokenman.search import Search
from tokenman.swap import Swap


# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == "__main__":
    args = parse_args()
    print(utils.BANNER)

    # Initialize logging level and format
    utils.init_logger(args.debug)

    # Create output directory: ./data/
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize tokenman state
    state = RunState(
        token_cache=TokenCache(
            access_token=args.access_token,
            refresh_token=args.refresh_token,
        ),
        output=output_dir,
        proxy=args.proxy,
    )

    # Handle 'fetch' command
    if args.command == "fetch":

        logging.debug(f"Fetch Modules: {args.module}")
        Fetch.run(
            state=state,
            modules=args.module,
        )

    # Handle 'search' command
    elif args.command == "search":

        logging.debug(f"Search Module: {args.module}")
        Search.run(
            state=state,
            modules=args.module,
            keywords=args.keyword,
        )

    # Handle 'swap' command
    elif args.command == "swap":

        logging.debug(f"Swap Target: {args.client_id}")
        Swap.run(
            state=state,
            client_id=args.client_id,
            resource=args.resource,
            scope=args.scope,
        )

    # Handle 'az' command
    elif args.command == "az":

        AZ.run(state=state, client_id=args.client_id)
