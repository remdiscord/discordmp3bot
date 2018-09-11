#! /usr/bin/env python

"""
mp3bot ~ cogs/player/__init__.py
Discord mp3 player cog

Copyright (c) 2017 Joshua Butt
"""

import asyncio
import json

from re import findall

import discord
from discord.ext import commands

from .config import *
from .player import Playlist, Session
from .search import *


class SearchConverter(commands.Converter):
    """Converts to subclass of :class:`Search`"""
    async def convert(self, ctx, argument):

        result = None
        for cls, search_type in search_types:
            if search_type == argument.lower():
                result = cls
                break

        if not issubclass(result, Search):
            raise commands.BadArgument(f'Search Type "{argument}" not found.')

        return result


# Command Checks
def _is_guild(ctx):
    """You must be in a server to use this command..."""
    return ctx.guild is not None


def _is_session(ctx):
    """There is currently no player running on this server..."""
    return ctx.cog._get_session(ctx) is not None


def _no_session(ctx):
    """There is already a player running on this server..."""
    return ctx.cog._get_session(ctx) is None


def _is_listening(ctx):
    """You are currently not listening to the player..."""
    return ctx.author in ctx.cog._get_session(ctx).listeners

def _is_admin(ctx):
    "You must be an administrator to use this command..."
    return ctx.author.guild_permissions.administrator or ctx.author.id == ctx.bot.owner_id


class Player:
    """MP3 and Requests Player"""

    def __init__(self, bot):
        self.bot = bot
        self.sessions = dict()

    def _get_session(self, ctx):
        return self.sessions.get(ctx.guild, None)

    # Player Commands

    @commands.command(name="skip")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_listening)
    async def player_skip_track(self, ctx):
        """Skips the currently playing track.

        In order to skip a track more than half of the current listeners must vote to skip.
        """
        session = self._get_session(ctx)
        listeners = session.listeners

        session.skip_requests = list(
            set(listeners) & set(session.skip_requests))
        count_needed = len(listeners) // 2 + 1

        # if already skipped
        if ctx.author in session.skip_requests:
            e = discord.Embed(title="Skip track request",
                              description="you have already requested to skip...", colour=0xe57a80)
        else:
            session.skip_requests.append(ctx.author)

        # if enough requests, listener alone or requester
        if len(session.skip_requests) >= count_needed or len(listeners) == 1 or session.current_track.requester == ctx.author:
            e = discord.Embed(title="Skip track request",
                              description="Skipping track...", colour=0x004d40)
            session.voice.stop()

        # if no-one has requested
        elif len(session.skip_requests) == 0:
            e = discord.Embed(title="Skip track request initiated...",
                              description=f"you currently need **{count_needed - len(session.skip_requests)}** more votes to skip this track.", colour=0x004d40)

        # otherwise show how many requests are required
        else:
            e = discord.Embed(title="Skip track request",
                              description=f"you currently need **{count_needed - len(session.skip_requests)}** more votes to skip this track.", colour=0x004d40)

        e.set_author(
            name=f"Skip request - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

    @commands.command(name="force_skip")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_admin)
    async def player_force_skip_track(self, ctx):
        """Force Skips the currently playing track."""
        session = self._get_session(ctx)

        e = discord.Embed(title="Skip track request",
                          description="Skipping track...", colour=0x004d40)
        e.set_author(
            name=f"Skip request - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

        session.voice.stop()

    @commands.command(name="repeat")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_listening)
    async def player_repeat_track(self, ctx):
        """Repeats the currently playing track.

        In order to repeat a track more than half of the current listeners must vote to repeat.
        """
        session = self._get_session(ctx)
        listeners = session.listeners

        session.repeat_requests = list(
            set(listeners) & set(session.repeat_requests))
        count_needed = len(listeners) // 2 + 1

        # if already skipped
        if ctx.author in session.repeat_requests:
            e = discord.Embed(title="Repeat track request",
                              description="you have already requested to repeat...", colour=0xe57a80)
        else:
            session.repeat_requests.append(ctx.author)

        # if enough requests, listener alone or requester
        if len(session.repeat_requests) >= count_needed or len(listeners) == 1 or session.current_track.requester == ctx.author:
            e = discord.Embed(title="Repeat track request",
                              description="Repeat track...", colour=0x004d40)
            session.playlist.add_request(session.current_track, front=True)

        # if no-one has requested
        elif len(session.repeat_requests) == 0:
            e = discord.Embed(title="Repeat track request initiated...",
                              description=f"you currently need **{count_needed - len(session.repeat_requests)}** more votes to repeat this track.", colour=0x004d40)

        # otherwise show how many requests are required
        else:
            e = discord.Embed(title="Repeat track request",
                              description=f"you currently need **{count_needed - len(session.repeat_requests)}** more votes to repeat this track.", colour=0x004d40)

        e.set_author(
            name=f"Repeat request - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

    @commands.command(name="force_repeat")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_admin)
    async def player_force_repeat_track(self, ctx):
        """Force Repeats the currently playing track."""
        session = self._get_session(ctx)

        e = discord.Embed(title="Repeat track request",
                          description="Repeating track...", colour=0x004d40)
        e.set_author(
            name=f"Repeat request - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

        session.playlist.add_request(session.current_track, front=True)

    @commands.command(name="request")
    @commands.check(_is_guild)
    async def player_request(self, ctx, search_type: SearchConverter, *, query: str = None):
        """Adds a specified request to the queue.

        Avaliable search types include:
        ```yaml
        MP3:        Search through the local song playlist
        YouTube:    Search for videos on YouTube
        SoundCloud: Search for songs on SoundCloud
        Clyp:       Play track from Clyp given a URL or ID
        ```
        """
        await ctx.trigger_typing()

        session = self._get_session(ctx)
        if session is None:
            if ctx.author.voice is not None:
                voice = await ctx.author.voice.channel.connect()
                session = Session(self.bot, self, voice)
                self.sessions[ctx.guild] = session
            else:
                raise TrackError("You are not in a voice channel...")

        vote_reaction_emojis = [
            (str(i).encode("utf-8") + b"\xe2\x83\xa3").decode("utf-8") for i in range(1, 9)]

        if len([track for track in session.playlist.requests if track.requester == ctx.author]) > 1:
            embed = discord.Embed(title="Your request cannot be processed",
                                  description=f"You can only request up-to two songs in advance...\nFor more information type `{ctx.prefix}help {ctx.command.name}`.", colour=0xe57a80)
            embed.set_author(
                name=f"Error: {ctx.command.name}", icon_url=ctx.bot.user.avatar_url)
            await ctx.send(embed=embed)
            return

        try:
            search = search_type(self.bot.log, query, ctx.author)
            await search.get()

            result_message = await ctx.send(**search.search_embed)

            for index, track in enumerate(search.tracks):
                await result_message.add_reaction(vote_reaction_emojis[index])

            # listen for reaction result
            def check(reaction, user):
                return all([
                    user == ctx.author,
                    reaction.message.id == result_message.id,
                    reaction.emoji in vote_reaction_emojis[:len(search.tracks)]
                ])
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60, check=check)
            except asyncio.TimeoutError:
                raise TrackError("You did not choose a track in time")

            await result_message.delete()
            track = search.tracks[int(reaction.emoji[0]) - 1]

            session.playlist.add_request(track)
            await ctx.send(**track.request_embed)

            if not session.is_playing:
                session.start()


        except Exception as e:
            self.bot.log.error(type(e).__name__ + ': ' + str(e))
            embed = discord.Embed(title="There was an error processing your request...",
                                  description=f"{e}\nFor more information type `{ctx.prefix}help {ctx.command.name}`.", colour=0xe57a80)
            embed.set_author(
                name=f"Error: {ctx.command.name}", icon_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name="volume")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_listening)
    async def player_set_volume(self, ctx, volume: float = None):
        """Sets the player volume.

        Play volume can be set between 0 and 1
        The defaule volume is 0.15
        """
        session = self._get_session(ctx)
        if volume is None or not 0 <= volume <= 1:
            session.change_volume(DEFAULT_VOLUME)
            embed = discord.Embed(title="Reseting volume to default...",
                                  description="Changing volume..", colour=0x004d40)

        else:
            session.change_volume(volume)
            embed = discord.Embed(
                title=f"Setting volume to {volume}...", description="Changing volume...", colour=0x004d40)

        embed.set_author(
            name=f"Volume change - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name="playing")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    async def player_get_current_track(self, ctx):
        """Displays the currently playing track."""
        session = self._get_session(ctx)
        await ctx.send(**session.current_track.playing_embed)

    @commands.command(name="queue")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    async def player_get_queue(self, ctx):
        """Retrieves the next 10 upcoming tracks."""
        session = self._get_session(ctx)
        embed = discord.Embed(
            title=f"{self.bot.user.name} Playlist for {ctx.guild.name} - Upcoming songs:", description="", colour=0x004d40)

        for track in session.playlist.queue:
            embed.add_field(**track.queue, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="stop_player")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_admin)
    async def player_stop_session(self, ctx):
        """Stops the player in the current guild."""
        session = self._get_session(ctx)
        session.stop()
        del self.sessions[ctx.guild.id]

    @commands.command(name="restart_player")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_admin)
    async def player_restart_session(self, ctx):
        """Restarts the player in the current guild."""
        old_session = self._get_session(ctx)
        old_session.stop()

        embed = discord.Embed(title="Restarting Player...",
                              description="restarting...", colour=0x004d40)
        embed.set_author(
            name=f"Player Restart - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

        session_config = {
            "bot": self.bot,
            "voice": await old_session.voice.channel.connect(),
            "cog": self
        }

        self.sessions[session_config["voice"].guild.id] = Session(
            **session_config)

    async def on_voice_state_update(self, member, before, after):
        try:
            await self._get_session(member).check_voice_state()
        except AttributeError:
            pass
        except Exception as e:
            self.bot.log.error(f"{type(e).__name__}: {e}")


def setup(bot):
    bot.add_cog(Player(bot))
