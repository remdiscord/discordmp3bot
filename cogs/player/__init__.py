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


class Player:
    """MP3 and Requests Player"""

    def __init__(self, bot):
        self.bot = bot
        self.sessions = dict()

    def _get_session(self, ctx):
        return self.sessions.get(ctx.guild.id, None)

    # Command Checks
    def _is_guild(ctx):
        """Check message is from a guild"""
        return ctx.guild is not None

    def _is_session(ctx):
        """Check There is a session running for the current guild"""
        return ctx.cog._get_session(ctx) is not None

    def _no_session(ctx):
        """Check There is a session running for the current guild"""
        return ctx.cog._get_session(ctx) is None

    def _is_listening(ctx):
        """Check message author is currently listening"""
        return ctx.author in ctx.cog._get_session(ctx).listeners

    def _has_permission(ctx):
        """Check message author has the required role to use player commands if role specified"""
        permissions = ctx.cog._get_session(
            ctx).permissions.get(ctx.command.name, None)
        return ctx.author.id == ctx.bot.owner_id or (permissions in ctx.author.roles if permissions else True)

    def _is_admin(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == ctx.bot.owner_id

    # Player Commands

    @commands.command(name="skip")
    @commands.check(_is_guild)
    @commands.check(_is_session)
    @commands.check(_is_listening)
    @commands.check(_has_permission)
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
    @commands.check(_has_permission)
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
    @commands.check(_is_session)
    @commands.check(_is_listening)
    @commands.check(_has_permission)
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
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
            except asyncio.TimeoutError:
                raise TrackError("You did not choose a track in time")

            await result_message.delete()
            track = search.tracks[int(reaction.emoji[0]) - 1]

            session.playlist.add_request(track)
            await ctx.send(**track.request_embed)

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
    @commands.check(_has_permission)
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

    @commands.command(name="start_player")
    @commands.check(_is_guild)
    @commands.check(_no_session)
    @commands.check(_is_admin)
    async def player_start_session(self, ctx, voice_channel: commands.converter.VoiceChannelConverter, *, log_channel=None):
        """Starts a new player given a voice and log channel."""

        try:
            log_channel = await commands.converter.TextChannelConverter().convert(ctx, log_channel)
        except commands.BadArgument:
            log_channel = None

        session_config = {
            "bot": self.bot,
            "voice": await voice_channel.connect(),
            "log_channel": log_channel,
            "playlist": Playlist(self.bot.log)
        }
        self.sessions[session_config["voice"].guild.id] = Session(
            **session_config)

    @commands.command(name="add_player")
    @commands.check(_is_guild)
    @commands.check(_is_admin)
    async def add_player_session(self, ctx, voice_channel: commands.converter.VoiceChannelConverter, *, log_channel=None):
        """Adds a player session to the startup list"""
        try:
            log_channel = await commands.converter.TextChannelConverter().convert(ctx, log_channel).id
        except commands.BadArgument:
            log_channel = None

        startup_list = json.load(open(SESSIONS_FILE))
        startup_list.append(
            {
                "voice_channel": voice_channel.id,
                "log_channel": log_channel
            }
        )
        json.dump(startup_list, open(SESSIONS_FILE, "w"))

        embed = discord.Embed(
            title="Permanently adding player...", description="saving...", colour=0x004d40)
        embed.set_author(
            name=f"Add Player - requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
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
            "log_channel": old_session.log_channel,
            "playlist": old_session.playlist,
            "permissions": old_session.permissions
        }

        self.sessions[session_config["voice"].guild.id] = Session(
            **session_config)

    async def on_ready(self):
        for session in INITIAL_SESSIONS:  # Start Inital player sessions

            try:
                session_config = {
                    "bot": self.bot,
                    "voice": await self.bot.get_channel(session["voice_channel"]).connect(),
                    "log_channel": self.bot.get_channel(session["log_channel"])
                }

                if session.get("playlist", None):
                    session_config["playlist"] = Playlist(
                        self.bot.log, **session["playlist"])
                else:
                    session_config["playlist"] = Playlist(self.bot.log)

                if session.get("permissions", None):
                    permissions = dict()
                    for command, role_id in session["permissions"].items():

                        try:
                            permissions[command] = next(
                                role for role in session_config["voice"].guild.roles if role.id == role_id)
                        except StopIteration as e:
                            self.bot.error.log(
                                f"Invalid Role ID assigned for permission: {command}")
                            raise e

                    session_config["permissions"] = permissions
                else:
                    permissions = None

                self.sessions[session_config["voice"].guild.id] = Session(
                    **session_config)

            except Exception as e:
                self.bot.log.error(
                    f"Failed to start session for channel: {session['voice_channel']}")
                self.bot.log.error(f"{type(e).__name__}: {e}")

    async def on_voice_state_update(self, member, before, after):
        try:
            await self._get_session(member).check_voice_state()
        except AttributeError:
            pass
        except Exception as e:
            self.bot.log.error(f"{type(e).__name__}: {e}")

    async def on_command_error(self, ctx, error):
        if isinstance(ctx.cog, self.__class__):
            if isinstance(error, commands.CheckFailure):
                check = next(
                    check for check in ctx.command.checks if not check(ctx))

                checks = {
                    self.__class__._is_guild: "You must be in a server to use this command...",
                    self.__class__._is_session: "There is currently no player running on this server...",
                    self.__class__._is_listening: "You are currently not listening to the player...",
                    self.__class__._has_permission: "You do not have permission to use this command...",
                    self.__class__._is_admin: "You must be an administrator to use this command...",
                }

                error = checks.get(check, None)
                if error:
                    e = discord.Embed(
                        title=error, description=f"for more information type `{ctx.prefix}help {ctx.command.name}`.", colour=0xe57a80)
                    e.set_author(
                        name=f"Error: {ctx.command.name}", icon_url=ctx.bot.user.avatar_url)

                await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Player(bot))
