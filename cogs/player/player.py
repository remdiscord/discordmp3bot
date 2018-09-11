#! /usr/bin/env python

"""
mp3bot ~ cogs/player/player.py
Discord mp3 player classes

Copyright (c) 2017 Joshua Butt
"""

import asyncio

from glob import glob
from random import shuffle
from re import findall

import discord
from discord.ext import commands

from .config import *
from .track import *


class Playlist:
    """mp3 playlist object"""

    def __init__(self, log, *, playlist_directory=None, cache_length=None):

        self.log = log
        self.playlist_directory = playlist_directory or DEFAULT_PLAYLIST_DIRECTORY

        self.tracks = self._get_tracks
        self.requests = list()
        self.playlist = list(self._get_new_track for track in range(
            cache_length or DEFAULT_CACHE_LENGTH))

    @property
    def _get_tracks(self):
        """Returns a list of mp3 files in the playlist directory"""
        files = glob(self.playlist_directory + "/*.mp3")
        shuffle(files)
        return files

    @property
    def _get_new_track(self):
        """Retruns the next item in the playlist as a :class:Mp3File"""
        try:
            return Mp3File(self.log, self.tracks.pop(0))
        except (IndexError, TrackError):
            self.tracks = self._get_tracks
            return self._get_new_track

    @property
    def queue(self):
        """Returns the next 10 items in the playlist queue"""
        return (self.requests + self.playlist)[:10]

    @property
    def next_track(self):
        """Returns the next track"""
        if self.requests:
            return self.requests.pop(0)
        self.playlist.append(self._get_new_track)
        return self.playlist.pop(0)

    def add_request(self, request, *, front=False):
        """Adds the requested song to the playlist"""
        if front:
            self.requests.insert(0, request)
        else:
            self.requests.append(request)


class RequestPlaylist:
    """Request only playlist object"""

    def __init__(self):
        self.requests = list()

    @property
    def queue(self):
        """Returns the next 10 items in the playlist queue"""
        return self.requests[:10]

    @property
    def next_track(self):
        """Returns the next track"""
        if self.requests:
            return self.requests.pop(0)
        else:
            return None

    def add_request(self, request, *, front=False):
        """Adds the requested song to the playlist"""
        if front:
            self.requests.insert(0, request)
        else:
            self.requests.append(request)


class Session:
    """Discord MP3Player session"""

    def __init__(self, bot, cog, voice, log_channel, *, playlist=None, permissions=None):

        self.bot = bot
        self.voice = voice
        self.cog = cog

        self.guild = self.voice.guild

        self.log_channel = log_channel
        self.playlist = playlist or RequestPlaylist()
        self.permissions = permissions or dict()

        self.is_playing = True
        self.current_track = None

        self.skip_requests = list()
        self.repeat_requests = list()
        self.volume = DEFAULT_VOLUME

        self.play_next_song = asyncio.Event()

        if playlist:
            self.player = self.bot.loop.create_task(self._player_task())

    @property
    def listeners(self):
        """Returns the list of current listeners"""
        listeners = [m for m in self.voice.channel.members if not (
            m.voice.self_deaf or m.voice.deaf)]
        return list(filter(self.voice.guild.me.__ne__, listeners))

    def start(self):
        """Starts the player"""
        self.is_playing = True
        self.player = self.bot.loop.create_task(self._player_task())

    def _toggle_next(self, error=None):
        """Plays the next song"""
        if error:
            self.bot.log.error(f"Error occured playing track: {error}")
        self.skip_requests = list()
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    def change_volume(self, volume):
        """Changes the player's volume"""
        self.volume = volume
        self.voice.source.volume = volume

    def stop(self):
        """Stops the player"""
        self.is_playing = False
        self.voice.stop()

    async def _play_track(self, track):
        """Plays the specified track"""
        self.current_track = track

        # Log track to log_channel
        if self.log_channel and self.is_playing:
            try:
                await self.log_channel.send(**self.current_track.playing_embed)
            except discord.Forbidden as e:
                self.bot.log.error(
                    "Failed to log current track to log_channel")
                self.bot.log.error(f"{type(e).__name__}: {e}")

        player = discord.PCMVolumeTransformer(
            self.current_track.player, self.volume)
        self.voice.play(source=player, after=self._toggle_next)

    async def check_voice_state(self):
        """Checks wether the player should be paused or resumed"""
        listeners = self.listeners
        server_muted = self.voice.channel.guild.me.voice.mute

        if len(listeners) != 0 and not self.voice.is_playing() and not server_muted:
            self.voice.resume()
        elif (len(listeners) == 0 and self.voice.is_playing()) or server_muted:
            self.voice.pause()

    async def _player_task(self):
        """Player's asyncio loop"""
        while self.is_playing:
            self.play_next_song.clear()
            next_track = self.playlist.next_track
            if next_track is not None:
                await self._play_track(next_track)
                await self.check_voice_state()
                await self.play_next_song.wait()
            else:
                self.stop()
        await self.voice.disconnect()
        del self.cog.sessions[self.guild]