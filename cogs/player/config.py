#! /usr/bin/env python

"""
mp3bot ~ cogs/player/config.py
Discord mp3 player config

Copyright (c) 2017 Joshua Butt
"""

import json

from os import path


# Default player config
DEFAULT_PLAYLIST_DIRECTORY = "lib/mp3"
DEFAULT_CACHE_LENGTH = 10
DEFAULT_VOLUME = 0.15

# Search result config
SEARCH_RESULT_LIMIT = 5

# Discord embed attachments
ART_NOT_FOUND_FILE = "lib/img/art_not_found.png"
YOUTUBE_LOGO_FILE = "lib/img/youtube.png"
SOUNDCLOUD_LOGO_FILE = "lib/img/soundcloud.png"
CLYP_LOGO_FILE = "lib/img/clyp.png"

# List of guilds to start bot on initially
SESSIONS_FILE = path.dirname(__file__) + "/startup.json"
INITIAL_SESSIONS = json.load(open(SESSIONS_FILE))

# Config for search
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_CLIENT_ID = "AIzaSyAy0v_6O8mynKHUpPc40fds7Q7M29c749E"

SOUNDCLOUD_CLIENT_ID = "a3e059563d7fd3372b49b37f00a00bcf"

