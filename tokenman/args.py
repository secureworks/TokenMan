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

import argparse
import json
import sys
from tokenman import __title__
from tokenman import __version__
from tokenman import utils


def parse_args() -> argparse.Namespace:
    """Parse command line arguments

    :returns: argparse namespace
    """
    parser = argparse.ArgumentParser(description=f"{__title__} -- v{__version__}")
    subparsers = parser.add_subparsers(help="Command", dest="command")

    # Shared flags
    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument("--debug", action="store_true", help="enable debugging")
    token_group = base_subparser.add_mutually_exclusive_group()
    token_group.add_argument(
        "-r",
        "--refresh-token",
        type=str,
        help="AAD refresh token",
    )
    token_group.add_argument(
        "-a",
        "--access-token",
        type=str,
        help="AAD access token",
    )
    base_subparser.add_argument(
        "--proxy",
        type=str,
        help="HTTP proxy url (e.g. http://127.0.0.1:8080)",
    )

    # Manage 'fetch' command
    # tokenman.py fetch -r/--refresh ... [-a/--access-token ...] -m/--module {all | drives,emails,groups,organizations,users}
    fetch_parser = subparsers.add_parser(
        "fetch", help="Retrieve data via Graph API", parents=[base_subparser]
    )
    fetch_parser.add_argument(
        "-m",
        "--module",
        type=str,
        default="all",
        help=(
            "fetch module(s) to run (comma delimited) "
            "(all | applications,drives,emails,groups,organizations,serviceprincipals,users) "
            "[default: all]"
        ),
    )

    # Manage 'search' command
    # tokenman.py search -r/--refresh ... [-a/--access-token ...] -m/--module {all | messages,onedrive,sharepoint} [-k/--keyword ...]
    search_parser = subparsers.add_parser(
        "search", help="Search content via Graph API", parents=[base_subparser]
    )
    search_parser.add_argument(
        "-m",
        "--module",
        type=str,
        default="all",
        help=(
            "search module(s) to run (comma delimited) "
            "(all | messages,onedrive,sharepoint) "
            "[default: all]"
        ),
    )
    search_parser.add_argument(
        "-k",
        "--keyword",
        type=str,
        default=",".join(utils.SEARCH_KEYWORDS),
        help="keyword(s) to search for (comma delimited) [default: password,username]",
    )

    # Manage 'swap' command
    # tokenman.py swap -r/--refresh ... [-a/--access-token ...] -c/--client-id ... [-r/--resource ...] [-s/--scope ...]
    swap_parser = subparsers.add_parser(
        "swap", help="Exchange a refresh token", parents=[base_subparser]
    )
    swap_parser.add_argument(
        "--list",
        action="store_true",
        help="list foci client id and name mapping",
    )
    swap_parser.add_argument(
        "-c",
        "--client-id",
        type=str,
        help="application client id or name to exchange token for",
    )
    swap_parser.add_argument(
        "--resource",
        type=str,
        help="token resource (audience)",
    )
    swap_parser.add_argument(
        "--scope",
        type=str,
        default=".default",
        help="token scope (comma delimited) [default: .default]",
    )

    # Manage 'az' command
    # tokenman.py az -r/--refresh ... [-a/--access-token ...] -c/--client-id ...
    az_parser = subparsers.add_parser(
        "az", help="Generate Azure CLI authentication files", parents=[base_subparser]
    )
    az_parser.add_argument(
        "-c",
        "--client-id",
        type=str,
        default="04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        help="application client id or name to exchange token for [default: Azure CLI]",
    )

    args = parser.parse_args()

    if not args.command:
        parser.error("token man command required")

    # Perform arg validation
    if args.command == "fetch":
        if not args.module:
            parser.error("-m/--module required for 'fetch' command")

        if args.module.lower() == "all":
            args.module = utils.FETCH_MODULES

        else:
            args.module = args.module.split(",")
            args.module = [m.lower() for m in args.module]

            if any(m not in utils.FETCH_MODULES for m in args.module):
                parser.error("invalid 'fetch' module provided")

        if len(args.module) == 0:
            parser.error("no valid module provided")

        # Require refresh OR access token
        if not args.refresh_token and not args.access_token:
            parser.error("-r/--refresh-token or -a/-access-token required for 'fetch' command")  # fmt: skip

    elif args.command == "search":
        if not args.module:
            parser.error("-m/--module required for 'search' command")

        if not args.keyword:
            parser.error("-k/--keyword required for 'search' command")

        args.keyword = args.keyword.split(",")

        if args.module.lower() == "all":
            args.module = utils.SEARCH_MODULES

        else:
            args.module = args.module.split(",")
            args.module = [m.lower() for m in args.module]

            if any(m not in utils.SEARCH_MODULES for m in args.module):
                parser.error("invalid 'search' module provided")

        if len(args.module) == 0:
            parser.error("no valid module provided")

        # Require refresh OR access token
        if not args.refresh_token and not args.access_token:
            parser.error("-r/--refresh-token or -a/-access-token required for 'search' command")  # fmt: skip

    elif args.command == "swap":
        if args.list:
            print(json.dumps(utils.FOCI_CLIENT_IDS, indent=4))
            sys.exit(0)

        if not args.client_id:
            parser.error("-c/--client-id required for 'swap' command")

        if args.scope:
            args.scope = args.scope.split(",")

        # Check client name, get client id
        if args.client_id in utils.FOCI_CLIENT_IDS.keys():
            args.client_id = utils.FOCI_CLIENT_IDS[args.client_id]

        else:
            # Validate client id if provided directly
            if args.client_id not in utils.FOCI_CLIENT_IDS.values():
                parser.error("invalid 'swap' client id/name")

        # Require refresh token for token exchange
        if not args.refresh_token:
            parser.error("-r/--refresh-token required for 'swap' command")

    elif args.command == "az":
        if not args.client_id:
            parser.error("-c/--client-id required for 'az' command")

        # Check client name, get client id
        if args.client_id in utils.FOCI_CLIENT_IDS.keys():
            args.client_id = utils.FOCI_CLIENT_IDS[args.client_id]

        else:
            # Validate client id if provided directly
            if args.client_id not in utils.FOCI_CLIENT_IDS.values():
                parser.error("invalid 'az' client id")

        # Require refresh token for token exchange
        if not args.refresh_token:
            parser.error("-r/--refresh-token required for 'az' command")

    return args
