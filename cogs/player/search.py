#! /usr/bin/env python

"""
mp3bot ~ cogs/player/search.py
Discord mp3 player search

Copyright (c) 2017 Joshua Butt
"""

import difflib
import re

from glob import glob

import discord
import pafy
import soundcloud

from apiclient.discovery import build
from apiclient.errors import HttpError

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

        for filename in glob(DEFAULT_PLAYLIST_DIRECTORY + "/*.mp3"):
            search_term = filename[len(DEFAULT_PLAYLIST_DIRECTORY):-4]
            search_term = re.sub(r"[^A-z\s]", '', search_term.lower())
            self.files[search_term] = filename

        for search_term in difflib.get_close_matches(re.sub(r"[^A-z\s]", '', self.search_query.lower()), self.files, n=SEARCH_RESULT_LIMIT, cutoff=0.1):
            try:
                self.tracks.append(Mp3File(self.log, self.files[search_term], requester=requester))
            except TrackError:
                pass


    @property
    def search_embed(self):
        track_list = ""
        for index, track in enumerate(self.tracks):
            track_list += f"{index+1} - {track.title} by {track.artist}\n"

        embed = discord.Embed(title=f"Results for search - Requested by {self.requester.name}", description=track_list, colour=0xe57a80)
        embed.set_author(name=f"Local Tracks - Results for search {self.search_query}", icon_url=self.requester.avatar_url)

        return {
            "embed": embed
        }

youtube_client = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_CLIENT_ID)

class YoutubeSearch(Search):
    def __init__(self, log, search_query, requester):
        global youtube_client

        self.log = log
        self.search_query = search_query
        self.requester = requester
        self.tracks = list()

        search_reponse = youtube_client.search().list(
            q=search_query,
            part="snippet",
            maxResults=7
        ).execute()

        videos = list()
        for search_result in search_reponse.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                videos.append(search_result["id"]["videoId"])

        search_reponse = youtube_client.videos().list(
            part="snippet,contentDetails", 
            id=','.join(videos)
        ).execute()

        for search_result in search_reponse.get("items", []):
            length = re.search(r"(\d+)M", search_result["contentDetails"]["duration"])
            if length is None or int(length.groups()[0]) < 10:
                self.tracks.append(YoutubeVideo(self.log, search_result, self.requester))

        self.tracks = self.tracks[:SEARCH_RESULT_LIMIT]

    @property
    def search_embed(self):
        track_list = ""
        for index, track in enumerate(self.tracks):
            track_list += f"{index+1} - {track.title} by {track.creator}\n"

        embed = discord.Embed(title=f"Results for search - Requested by {self.requester.name}", description=track_list, colour=0xf44336)
        embed.set_author(name=f"YouTube - Results for search {self.search_query}", icon_url="attachment://youtube.png")

        return {
            "embed": embed, 
            "file": discord.File(open(YOUTUBE_LOGO_FILE, 'rb'), "youtube.png")
        }


soundcloud_client = soundcloud.Client(client_id=SOUNDCLOUD_CLIENT_ID)

class SoundCloudSearch(Search):
    """Class containing search configuration for SoundCloud"""
    def __init__(self, log, search_query, requester):
        global soundcloud_client

        self.client = soundcloud_client
        self.log = log
        self.search_query = search_query
        self.requester = requester

        search_results = self.client.get('/tracks', q=self.search_query)
        self.tracks = [SoundCloudTrack(self.log, track, self.requester) for track in search_results[:SEARCH_RESULT_LIMIT]]

    @property
    def search_embed(self):
        track_list = ""
        for index, track in enumerate(self.tracks):
            track_list += f"{index+1} - {track.title} by {track.creator}\n"

        embed = discord.Embed(title=f"Results for search - Requested by {self.requester.name}", description=track_list, colour=0xff9800)
        embed.set_author(name=f"SoundCloud - Results for search {self.search_query}", icon_url="attachment://soundcloud.png")

        return {
            "embed": embed, 
            "file": discord.File(open(SOUNDCLOUD_LOGO_FILE, 'rb'), "soundcloud.png")
        }


search_types = [
    (Mp3FileSearch, "mp3"),
    (YoutubeSearch, "youtube"),
    (SoundCloudSearch, "soundcloud")
]