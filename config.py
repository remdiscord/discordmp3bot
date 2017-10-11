#! /usr/bin/env python

"""
mp3bot ~ config.py
Basic configuration for bot

Copyright (c) 2017 Joshua Butt
"""

from secrets import TOKEN, OWNER_ID

# Application Name
APP_NAME = "mp3bot"

# Bot Debug toggle
DEBUG = False

# Is bot a selfbot
IS_SELFBOT = False

# Bot command Prefix
COMMAND_PREFIX = '!;'

# Initial cogs
INITIAL_COGS = [
    # Key components
    "cogs.admin",
    "cogs.utils.help",

    # Player cog
    "cogs.player"

]