#! /usr/bin/env python

"""
mp3bot ~ cogs/player/config.py
Discord mp3 player config

Copyright (c) 2017 Joshua Butt
"""

import json

from os import path


# Default player config
DEFAULT_VOLUME = 0.15

# Search result config
SEARCH_RESULT_LIMIT = 5

# Discord embed attachments
YOUTUBE_LOGO_FILE = "lib/img/youtube.png"
CLYP_LOGO_FILE = "lib/img/clyp.png"

# Config for search
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
# - Make sure you generate you're own ID for your bot
YOUTUBE_API_KEY = "AIzaSyAy0v_6O8mynKHUpPc40fds7Q7M29c749E"
