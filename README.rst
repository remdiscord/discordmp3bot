mp3bot
==========

mp3bot is a music player bot for discord using ``discord.py``

Features
------------

* Mp3 Player
* Youtube request functionality

Usage
------------
1. create ``cogs/player/startup.json`` to set up where the bot should play by default. e.g:

.. code:: json

    [
        {
            "voice_channel": 141045545992060929,
            "log_channel": 294154647759880192,
            "playlist": {
                "playlist_directory": "lib/mp3",
                "cache_length": 10
            },
            "permissions": {
                "skip": 321264380752822272,
                "request": 321264380752822272,
                "volume": 321264380752822272
            }
        },
        {
            "voice_channel": 290814653737467904,
            "log_channel": 290845622389440515,
        }
    ]

* ``playlist`` and ``permissions`` are optional

2. create ``secrets.py``

* This should include both your bot's ``TOKEN`` and ``OWNER_ID``

3. modify ``config.py`` to suit your preferences

4. run ``bot.py``

Requirements
------------
* python 3.6.2+
*  ``discord.py`` `library <https://github.com/Rapptz/discord.py/tree/rewrite>`_
* ``pafy`` library
* ``mutagen`` library
* ``google-api-python-client`` library
* ``soundcloud`` library

You can get these via ``pip``