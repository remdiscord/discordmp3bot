#! /usr/bin/env python

"""
mp3bot ~ cogs/player/mp3file.py
mp3 file class

Copyright (c) 2017 Joshua Butt
"""

from mutagen.mp3 import MP3

from .config import *


class Mp3File:
    """Class containing metadata for MP3 file"""
    def __init__(self, file, log):
        self.file = file
        mp3_file = MP3(self.file)
        self.log = log

        tags = [
            ['title', u'TIT2'], ['album', u'TALB'],
            ['artist', u'TPE1'], ['date', u'TDRC'],
        ]
        # Strip MP3 metadata
        for var, tag in tags:
            try:
                setattr(self, var, mp3_file.tags[tag][0])
            except KeyError:
                self.log.warning(f"Failed to find {var} for {self.file}")
                setattr(self, var, "???")
            except TypeError:
                self.log.error(f"Failed to load track {track.file}")

        # Find album artwork
        try:
            self.cover = mp3_file[u'APIC:'].data
        except KeyError as e:
            self.log.warning(f"Failed to find cover for {self.file}")
            self.cover = open(ART_NOT_FOUND_FILE, 'rb')