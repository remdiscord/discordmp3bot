#! /usr/bin/env python

"""
mp3bot ~ cogs/player/search.py
Discord mp3 player search

Copyright (c) 2017 Joshua Butt
"""

import aiohttp
import difflib
import re

from glob import glob

import discord

from .config import *
from .track import *

__all__ = [
    "Search",

    "SearchError",
    "TrackError",

    "search_types"
]


class SearchError(Exception):
    """"""
    pass


class Search:
    """Base class for various audio track types"""

    @property
    def search_embed(self):
        """Returns an instance of :class:`discord.Embed`"""
        raise NotImplementedError


class Mp3FileSearch(Search):
    def __init__(self, log, search_query, requester):

        self.log = log
        self.search_query = search_query
        self.requester = requester
        self.files = dict()
        self.tracks = list()

    async def get(self):
        for filename in glob(DEFAULT_PLAYLIST_DIRECTORY + "/*.mp3"):
            search_term = filename[len(DEFAULT_PLAYLIST_DIRECTORY):-4]
            search_term = re.sub(r"[^A-z\s]", '', search_term.lower())
            self.files[search_term] = filename

        for search_term in difflib.get_close_matches(re.sub(r"[^A-z\s]", '', self.search_query.lower()), self.files, n=SEARCH_RESULT_LIMIT, cutoff=0.1):
            try:
                self.tracks.append(
                    Mp3File(self.log, self.files[search_term], requester=self.requester))
            except TrackError:
                pass

    @property
    def search_embed(self):
        track_list = ""
        for index, track in enumerate(self.tracks):
            track_list += f"{index+1} - {track.title} by {track.artist}\n"

        embed = discord.Embed(
            title=f"Results for search - Requested by {self.requester.name}", description=track_list, colour=0xe57a80)
        embed.set_author(
            name=f"Local Tracks - Results for search {self.search_query}", icon_url=self.requester.avatar_url)

        return {
            "embed": embed
        }


class YoutubeSearch(Search):
    def __init__(self, log, search_query, requester):
        self.log = log
        self.search_query = search_query
        self.requester = requester
        self.tracks = list()

    async def get(self):
        videos = list()
        youtube_api_url = f"https://www.googleapis.com/{YOUTUBE_API_SERVICE_NAME}/{YOUTUBE_API_VERSION}"
        youtube_search_url = f"{youtube_api_url}/search?q={self.search_query}&part=snippet&maxResults=7&key={YOUTUBE_API_KEY}&alt=json"

        async with aiohttp.ClientSession() as session:
            async with session.get(youtube_search_url) as resp:

                if resp.status != 200:
                    self.log.error(
                        f"Error querying youtube API, likely bad API key")
                    raise Exception(
                        "Error querying youtube API, likely bad API key")

                for search_result in await resp.json()["items"]:
                    if search_result["id"]["kind"] == "youtube#video":
                        videos.append(search_result["id"]["videoId"])

        youtube_video_list_url = f"{youtube_api_url}/videos?part=snippet%2CcontentDetails&id={'%2C'.join(videos)}&key={YOUTUBE_API_KEY}&alt=json"

        async with aiohttp.ClientSession() as session:
            async with session.get(youtube_video_list_url) as resp:

                if resp.status != 200:
                    self.log.error(
                        f"Error querying youtube API, likely bad API key")
                    raise Exception(
                        "Error querying youtube API, likely bad API key")

                for search_result in await resp.json()["items"]:
                    hour_length = re.search(
                        r"(\d+)H", search_result["contentDetails"]["duration"])
                    if hour_length:
                        continue

                    minute_length = re.search(
                        r"(\d+)M", search_result["contentDetails"]["duration"])
                    if minute_length is None or int(minute_length.groups()[0]) < 10:
                        self.tracks.append(YoutubeVideo(
                            self.log, search_result, self.requester))

        self.tracks = self.tracks[:SEARCH_RESULT_LIMIT]

    @property
    def search_embed(self):
        track_list = ""
        for index, track in enumerate(self.tracks):
            track_list += f"{index+1} - {track.title} by {track.creator}\n"

        embed = discord.Embed(
            title=f"Results for search - Requested by {self.requester.name}", description=track_list, colour=0xf44336)
        embed.set_author(
            name=f"YouTube - Results for search {self.search_query}", icon_url="attachment://youtube.png")

        return {
            "embed": embed,
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }


class ClypSearch(Search):
    """Class containing search configuration for Clyp"""

    def __init__(self, log, search_query, requester):
        self.log = log
        self.search_query = search_query
        self.requester = requester

    async def get(self):
        track = re.search(
            r"(?:(?:clyp\.it\/)|^)([A-z\d]+)(?:$|\#)", self.search_query)
        if track is None:
            raise SearchError("Unable to find clyp with given ID or URL")

        self.track_id = track.groups()[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.clyp.it/{self.track_id}") as resp:
                if resp.status != 200:
                    raise SearchError(
                        "Unable to find clyp with given ID or URL")

                self.tracks = [ClypTrack(self.log, await resp.json(), self.requester)]

    @property
    def search_embed(self):
        track = f"{self.tracks[0].title}"

        embed = discord.Embed(
            title=f"Results for search - Requested by {self.requester.name}", description=track, colour=0x009688)
        embed.set_author(
            name=f"Clyp - Track ID: {self.track_id}", icon_url="attachment://clyp.png")

        return {
            "embed": embed,
            "file": discord.File(open(CLYP_LOGO_FILE, 'rb'), "clyp.png")
        }


search_types = [
    (Mp3FileSearch, "mp3"),
    (YoutubeSearch, "youtube"),
    (ClypSearch, "clyp")
]
