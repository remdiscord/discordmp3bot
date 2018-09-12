#! /usr/bin/env python

"""
mp3bot ~ cogs/player/track.py
Audio track classes

Copyright (c) 2017 Joshua Butt
"""

import discord
import pafy

from .config import *

__all__ = [
    'YoutubeVideo',
    'ClypTrack',

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
    def request_embed(self):
        """Returns an instance of :class:`discord.Embed`"""
        raise NotImplementedError

    @property
    def playing_embed(self):
        """Returns an instance of :class:`discord.Embed`"""
        raise NotImplementedError

    @property
    def queue(self):
        """Returns a string containg information to be displayed in the upcoming queue"""
        raise NotImplementedError


class YoutubeVideo(Track):
    """Class containing metadata for a YouTube video"""

    def __init__(self, log, video, requester):

        self.video = video

        self.title = self.video["snippet"]["title"]
        self.creator = self.video["snippet"]["channelTitle"]
        self.url = f"https://youtu.be/{self.video['id']}"
        self.thumbnail = self.video["snippet"]["thumbnails"]["default"]["url"]

        self.requester = requester

    @property
    def player(self):
        player = pafy.new(self.url)
        return discord.FFmpegPCMAudio(player.getbestaudio().url, options="-vn -b:a 192k")

    @property
    def request_embed(self):
        embed = discord.Embed(title="YouTube track request...",
                              description=f"adding **{self.title}** by **{self.creator}** to the queue...", colour=0xf44336)
        embed.set_author(
            name=f"Youtube Video - requested by {self.requester.name}", url=self.url, icon_url="attachment://youtube.png")
        embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed,
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }

    @property
    def playing_embed(self):
        embed = discord.Embed(
            title=self.title, description=self.creator, colour=0xf44336)
        embed.set_author(
            name=f"Youtube Video - requested by {self.requester.name}", url=self.url, icon_url="attachment://youtube.png")
        embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed,
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }

    @property
    def queue(self):
        return {
            "name": self.title,
            "value": f"{self.creator} - requested by - {self.requester.name}"
        }


class ClypTrack(Track):
    """Class containing metadata for a Clyp Track"""

    def __init__(self, log, track, requester):

        self.track = track

        self.title = self.track["Title"]
        self.url = f"https://clyp.it/{self.track['AudioFileId']}"

        self.thumbnail = self.track.get("ArtworkPictureUrl", None)

        self.requester = requester

    @property
    def player(self):
        return discord.FFmpegPCMAudio(self.track["Mp3Url"], options="-vn -b:a 192k")

    @property
    def request_embed(self):
        embed = discord.Embed(title="Clyp track request...",
                              description=f"adding **{self.title}** to the queue...", colour=0x009688)
        embed.set_author(
            name=f"Clyp - requested by {self.requester.name}", url=self.url, icon_url="attachment://clyp.png")
        if self.thumbnail is not None:
            embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed,
            "file": discord.File(open(CLYP_LOGO_FILE, 'rb'), "clyp.png")
        }

    @property
    def playing_embed(self):
        embed = discord.Embed(title=self.title, colour=0x009688)
        embed.set_author(
            name=f"Clyp Track - requested by {self.requester.name}", url=self.url, icon_url="attachment://clyp.png")
        if self.thumbnail is not None:
            embed.set_thumbnail(url=self.thumbnail)
        return {
            "embed": embed,
            "file": discord.File(open(CLYP_LOGO_FILE, 'rb'), "clyp.png")
        }

    @property
    def queue(self):
        return {
            "name": self.title,
            "value": f"requested by - {self.requester.name}"
        }
