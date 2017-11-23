#! /usr/bin/env python

"""
mp3bot ~ cogs/player/track.py
Audio track classes

Copyright (c) 2017 Joshua Butt
"""

import discord
import pafy
import soundcloud

from mutagen.mp3 import MP3

from .config import *

__all__ = [
    'Mp3File',
    'YoutubeVideo',
    'SoundCloudTrack',

    'TrackError'
]

class TrackError(Exception):
    """"""
    pass

class Track:
    """Base class for various audio track types"""

    @property
    def player(self):
        """Returns an instance of :class:`discord.FFmpegPCMAudio`"""
        raise NotImplementedError

    @property
    def embed(self):
        """Returns an instance of :class:`discord.Embed`"""
        raise NotImplementedError

    @property
    def queue(self):
        """Returns a string containg information to be displayed in the upcoming queue"""
        raise NotImplementedError

# - Local MP3 File

class Mp3File(Track):
    """Class containing metadata for MP3 file"""
    def __init__(self, file, log):
        self.file = file
        self.filename = self.file.encode("utf-8", 'ignore')
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
                self.log.warning(f"Failed to find {var} for {self.filename}")
                setattr(self, var, "???")
            except TypeError:
                self.log.error(f"Failed to load track {self.filename}")
                raise TrackError("Possibly corrupt MP3 tag")

        # Find album artwork
        try:
            self.cover = mp3_file[u'APIC:'].data
        except KeyError as e:
            self.log.warning(f"Failed to find cover for {self.filename}")
            self.cover = open(ART_NOT_FOUND_FILE, 'rb')

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

# - Youtube Video

class YoutubeVideo(Track):
    """Class containing metadata for a YouTube video"""
    def __init__(self, video_id, requester):
        try:
            self.video = pafy.new(f"https://youtu.be/{video_id}")
        except Exception as e:
            self.log.error(f"Failed to load youtube video: {video_id}")
            raise TrackError("Unable to find youtube video") from e

        self.title = self.video.title
        self.creator = self.video.author
        self.url = f"https://youtu.be/{video_id}"
        self.thumbnail = self.video.bigthumb

        self.requester = requester

    @property
    def player(self):
        return discord.FFmpegPCMAudio(self.video.getbestaudio().url, options="-bufsize 7680k")

    @property
    def embed(self):
        embed = discord.Embed(title=self.title, description=self.creator, colour=0xf44336)
        embed.set_author(name=f"Youtube Video - requested by {self.requester.name}", url=self.url, icon_url="attachment://youtube.png")
        embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed, 
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }

    @property
    def queue(self):
        return f"{self.creator} - requested by - {self.requester.name}"

# - Soundcloud track

soundcloud_client = soundcloud.Client(client_id=SOUNDCLOUD_CLIENT_ID)

class SoundCloudTrack(Track):
    """Class containing metadata for a YouTube video"""
    def __init__(self, search_term, requester):
        global soundcloud_client
        try:
            self.track = soundcloud_client.get('/tracks', q=search_term)[0]
        

            self.title = self.track.title
            self.creator = self.track.user["username"]
            self.url = self.track.permalink_url
            self.thumbnail = self.track.artwork_url

            self.requester = requester
        except Exception as e:
            raise TrackError from e

    @property
    def player(self):
        return discord.FFmpegPCMAudio(f"{self.track.stream_url}?client_id={SOUNDCLOUD_CLIENT_ID}", options="-bufsize 7680k")

    @property
    def embed(self):
        embed = discord.Embed(title=self.title, description=self.creator, colour=0xf44336)
        embed.set_author(name=f"SoundCloud Track - requested by {self.requester.name}", url=self.url, icon_url="attachment://soundcloud.png")
        embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed, 
            "file": discord.File(open(SOUNDCLOUD_LOGO_FILE, 'rb'), "soundcloud.png")
        }

    @property
    def queue(self):
        return f"{self.creator} - requested by - {self.requester.name}"