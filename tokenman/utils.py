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

# fmt: off

import base64
import json
import jwt  # type: ignore
import logging
import sys
from colorama import init  # type: ignore
from colorama import Fore  # type: ignore
from tokenman import __version__
from typing import Any
from typing import Dict


# Init colorama to switch between Windows and Linux
if sys.platform == "win32":
    init(convert=True)


FETCH_MODULES = [
    "applications",
    "drives",
    "emails",
    "groups",
    "organizations",
    "serviceprincipals",
    "users",
]

SEARCH_MODULES = [
    "messages",
    "onedrive",
    "sharepoint",
]

# Default search keywords
SEARCH_KEYWORDS = [
    "password",
    "username",
]

# FOCI application client ID map
FOCI_CLIENT_IDS = {
    "Accounts Control UI":                      "a40d7d7d-59aa-447e-a655-679a4107e548",
    "Microsoft Authenticator App":              "4813382a-8fa7-425e-ab75-3b753aab3abb",
    "Microsoft Azure CLI":                      "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    "Microsoft Azure PowerShell":               "1950a258-227b-4e31-a9cf-717495945fc2",
    "Microsoft Bing Search for Microsoft Edge": "2d7f3606-b07d-41d1-b9d2-0d0c9296a6e8",
    "Microsoft Bing Search":                    "cf36b471-5b44-428c-9ce7-313bf84528de",
    "Microsoft Edge":                           "f44b1140-bc5e-48c6-8dc0-5cf5a53c0e34",
    "Microsoft Edge (1)":                       "e9c51622-460d-4d3d-952d-966a5b1da34c",
    "Microsoft Edge AAD BrokerPlugin":          "ecd6b820-32c2-49b6-98a6-444530e5a77a",
    "Microsoft Flow":                           "57fcbcfa-7cee-4eb1-8b25-12d2030b4ee0",
    "Microsoft Intune Company Portal":          "9ba1a5c7-f17a-4de9-a1f1-6178c8d51223",
    "Microsoft Office":                         "d3590ed6-52b3-4102-aeff-aad2292ab01c",
    "Microsoft Planner":                        "66375f6b-983f-4c2c-9701-d680650f588f",
    "Microsoft Power BI":                       "c0d2a505-13b8-4ae0-aa9e-cddd5eab0b12",
    "Microsoft Stream Mobile Native":           "844cca35-0656-46ce-b636-13f48b0eecbd",
    "Microsoft Teams - Device Admin Agent":     "87749df4-7ccf-48f8-aa87-704bad0e0e16",
    "Microsoft Teams":                          "1fec8e78-bce4-4aaf-ab1b-5451cc387264",
    "Microsoft To-Do client":                   "22098786-6e16-43cc-a27d-191a01a1e3b5",
    "Microsoft Tunnel":                         "eb539595-3fe1-474e-9c1d-feb3625d1be5",
    "Microsoft Whiteboard Client":              "57336123-6e14-4acc-8dcf-287b6088aa28",
    "Office 365 Management":                    "00b41c95-dab0-4487-9791-b9d2c32c80f2",
    "Office UWP PWA":                           "0ec893e0-5785-4de6-99da-4ed124e5296c",
    "OneDrive iOS App":                         "af124e86-4e96-495a-b70a-90f90ab96707",
    "OneDrive SyncEngine":                      "ab9b8c07-8f02-4f72-87fa-80105867a763",
    "OneDrive":                                 "b26aadf8-566f-4478-926f-589f601d9c74",
    "Outlook Mobile":                           "27922004-5251-4030-b22d-91ecd9a37ea4",
    "PowerApps":                                "4e291c71-d680-4d0e-9640-0a3358e31177",
    "SharePoint Android":                       "f05ff7c9-f75a-4acd-a3b5-f4b6a870245d",
    "SharePoint":                               "d326c1ce-6cc6-4de2-bebc-4591e5e13ef0",
    "Visual Studio":                            "872cd9fa-d31f-45e0-9eab-6e460a02d1f1",
    "Windows Search":                           "26a7ee05-5602-4d76-a7ba-eae8b7b67941",
    "Yammer iPhone":                            "a569458c-7f2b-45cb-bab9-b7dee514d112",
}

BANNER = f"""
                :
               t#,     G:              ,;L.                                               L.
              ;##W.    E#,    :      f#i EW:        ,ft {Fore.RED}                    {Fore.RESET}              EW:        ,ft
  GEEEEEEEL  :#L:WE    E#t  .GE    .E#t  E##;       t#E {Fore.RED}          ..       :{Fore.RESET}           .. E##;       t#E
  ,;;L#K;;. .KG  ,#D   E#t j#K;   i#W,   E###t      t#E {Fore.RED}         ,W,     .Et{Fore.RESET}          ;W, E###t      t#E
     t#E    EE    ;#f  E#GK#f    L#D.    E#fE#f     t#E {Fore.RED}        t##,    ,W#t{Fore.RESET}         j##, E#fE#f     t#E
     t#E   f#.     t#i E##D.   :K#Wfff;  E#t D#G    t#E {Fore.RED}       L###,   j###t{Fore.RESET}        G###, E#t D#G    t#E
     t#E   :#G     GK  E##Wi   i##WLLLLt E#t  f#E.  t#E {Fore.RED}     .E#j##,  G#fE#t{Fore.RESET}      :E####, E#t  f#E.  t#E
     t#E    ;#L   LW.  E#jL#D:  .E#L     E#t   t#K: t#E {Fore.RED}    ;WW; ##,:K#i E#t{Fore.RESET}     ;W#DG##, E#t   t#K: t#E
     t#E     t#f f#:   E#t ,K#j   f#E:   E#t    ;#W,t#E {Fore.RED}   j#E.  ##f#W,  E#t{Fore.RESET}    j###DW##, E#t    ;#W,t#E
     t#E      f#D#;    E#t   jD    ,WW;  E#t     :K#D#E {Fore.RED} .D#L    ###K:   E#t{Fore.RESET}   G##i,,G##, E#t     :K#D#E
     t#E       G#t     j#t          .D#; E#t      .E##E {Fore.RED}:K#t     ##D.    E#t{Fore.RESET} :K#K:   L##, E#t      .E##E
      fE        t       ,;            tt ..         G#E {Fore.RED}...      #G      ...{Fore.RESET};##D.    L##, ..         G#E
       :                                             fE {Fore.RED}         j          {Fore.RESET},,,      .,,              fE
                                                      , {Fore.RED}                    {Fore.RESET}                           ,
                        v{__version__}

"""

class bcolors:
    """Color codes for colorized terminal output"""

    HEADER  = Fore.MAGENTA
    OKBLUE  = Fore.BLUE
    OKCYAN  = Fore.CYAN
    OKGREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    FAIL    = Fore.RED
    ENDC    = Fore.RESET


class LoggingLevels:
    CRITICAL = f"{bcolors.FAIL}%s{bcolors.ENDC}" % "crit"
    WARNING  = f"{bcolors.WARNING}%s{bcolors.ENDC}" % "warn"
    DEBUG    = f"{bcolors.OKBLUE}%s{bcolors.ENDC}" % "debug"
    ERROR    = f"{bcolors.FAIL}%s{bcolors.ENDC}" % "fail"
    INFO     = f"{bcolors.OKGREEN}%s{bcolors.ENDC}" % "info"


def init_logger(debug: bool):
    """Initialize program logging

    :param debug: debug enabled/disabled
    """
    if debug:
        logging_level = logging.DEBUG
        logging_format = ("[%(asctime)s] [%(levelname)-5s] %(filename)17s:%(lineno)-4s - %(message)s")
    else:
        logging_level = logging.INFO
        logging_format = "[%(asctime)s] [%(levelname)-5s] %(message)s"

    logging.basicConfig(format=logging_format, level=logging_level)

    # Handle color output
    logging.addLevelName(logging.CRITICAL, LoggingLevels.CRITICAL)
    logging.addLevelName(logging.WARNING, LoggingLevels.WARNING)
    logging.addLevelName(logging.DEBUG, LoggingLevels.DEBUG)
    logging.addLevelName(logging.ERROR, LoggingLevels.ERROR)
    logging.addLevelName(logging.INFO, LoggingLevels.INFO)

def pad_base64(data: str) -> str:
    """Pad a Base64 string

    :param data: base64 encoded string
    :returns: padded base64 encoded string
    """
    data = data + ("=" * (4 - (len(data) % 4)))
    return data

def base64_to_json(data: str) -> Dict[Any, Any]:
    """Base64 decode JSON string and convert to Python
    dictionary

    Leave error handling to the calling functions for
    more clear error output

    :param data: base64 encoded string
    :returns: json dictionary
    """
    data = base64.b64decode(data)
    data = json.loads(data)
    return data

def decode_jwt(token: str) -> Dict[Any, Any]:
    """Decode access token JWT

    Leave error handling to the calling functions for
    more clear error output

    :param token: access token
    :returns: decoded jwt payload
    """
    payload = jwt.decode(
        token,
        algorithms=["RS256"],
        options={"verify_signature": False}
    )
    return payload
