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

# Discord embed attachments
ART_NOT_FOUND_FILE = "lib/img/art_not_found.png"
YOUTUBE_LOGO_FILE = "lib/img/youtube.png"


# List of guilds to start bot on initially
SESSIONS_FILE = path.dirname(__file__) + "/startup.json"
INITIAL_SESSIONS = json.load(open(SESSIONS_FILE))