#! /usr/bin/env python

"""
mp3bot ~ cogs/player/track.py
mp3 file class

Copyright (c) 2017 Joshua Butt
"""

import discord
import pafy

from mutagen.mp3 import MP3

from .config import *

__all__ = [
    'Mp3File',
    'YoutubeVideo'
]

class Track:
    """Base class for various audio track types"""
    @property
    def player(self):
        raise NotImplementedError

    @property
    def embed(self):
        raise NotImplementedError

    @property
    def queue(self):
        raise NotImplementedError

class Mp3File(Track):
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
            self.cover = open(ART_NOT_FOUND_FILE, 'rb')\

    @property
    def player(self):
        return discord.FFmpegPCMAudio(self.file)

    @property
    def embed(self):
        embed = discord.Embed(title=self.title, description=f"{self.album} - ({self.date})", colour=0x009688)
        embed.set_author(name=self.artist)
        embed.set_thumbnail(url="attachment://cover.jpg")
        return {
            "embed": embed, 
            "file": discord.File(self.cover, "cover.jpg")
        }

    @property
    def queue(self):
        return f"{self.artist}: {self.album} - ({self.date})"

class YoutubeVideo(Track):
    def __init__(self, video_id, requester):
        self.video = pafy.new("https://youtu.be/" + video_id)

        self.title = self.video.title
        self.creator = self.video.author
        self.video_id = self.video.videoid
        self.thumbnail = self.video.bigthumb

        self.requester = requester

    @property
    def player(self):
        return discord.FFmpegPCMAudio(self.video.getbestaudio().url, options="-bufsize 7680k")

    @property
    def embed(self):
        embed = discord.Embed(title=self.title, description=self.creator, colour=0xf44336)
        embed.set_author(name=f"Youtube Video - requested by {self.requester.name}", url=f"https://youtu.be/{self.video_id}", icon_url="attachment://youtube.png")
        embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed, 
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }

    @property
    def queue(self):
        return f"{self.creator} - requested by - {self.requester.name}"