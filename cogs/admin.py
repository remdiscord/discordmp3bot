#! /usr/bin/env python

"""
mp3bot ~ cogs/admin.py
Discord administration cog

Copyright (c) 2017 Joshua Butt
"""
import asyncio
import inspect
import os
import re

import discord
from discord.ext import commands


class Admin:
    
    def __init__(self, bot):
        self.bot = bot

    async def _response(self, ctx, title:str, *, description:str=None, colour=None, timeout=3):
        """Send embed message response"""
        embed_message = discord.Embed(title=title, description=description, colour=colour)

        if self.bot.user.bot:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            response = await ctx.send(embed=embed_message)
        else:
            response = ctx.message
            await response.edit(content=None, embed=embed_message)

        if timeout:
            await asyncio.sleep(timeout)
            await response.delete()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def load(self, ctx, cog:str):
        """Loads a specified cog"""
        cog = f"cogs.{cog}"
        try:
            self.bot.load_extension(cog)
            await self._response(ctx, f"Succesfully loaded module: {cog}", colour=0x009688, timeout=2)
        except Exception as e:
            await self._response(ctx, f"Failed to load module: {cog}", description=f"{type(e).__name__}: {e}", colour=0xf44336, timeout=5)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def unload(self, ctx, cog:str):
        """Unloads a specified cog"""
        cog = f"cogs.{cog}"
        try:
            self.bot.unload_extension(cog)
            await self._response(ctx, f"Succesfully unloaded module: {cog}", colour=0x009688, timeout=2)
        except Exception as e:
            await self._response(ctx, f"Failed to unload module: {cog}", description=f"{type(e).__name__}: {e}", colour=0xf44336, timeout=5)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def reload(self, ctx, cog:str):
        """Reloads a specified cog"""
        cog = f"cogs.{cog}"
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
            await self._response(ctx, f"Succesfully reloaded module: {cog}", colour=0x009688, timeout=2)
        except Exception as e:
            await self._response(ctx, f"Failed to reload module: {cog}", description=f"{type(e).__name__}: {e}", colour=0xf44336, timeout=5)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def eval(self, ctx, *, code:str):
        """Evaulates python code"""
        
        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'message': ctx.message,
            'author': ctx.author,
            'channel': ctx.channel,
            'guild': ctx.guild,
        }
        env.update(globals())

        exec_test = re.compile(r"(?:^(?:(?:for)|(?:def)|(?:while)|(?:if)))|(?:^([a-z_][A-z0-9_\-\.]*)\s?(?:\+|-|\\|\*)?=)")
        commands = []

        for command in code.split(';'):
            try:
                command = command.strip()
                is_exec = exec_test.match(command)

                if is_exec:
                    exec(command, env)
                    result = env.get(is_exec.group(1), None)
                    if inspect.isawaitable(result):
                        result = await result
                        env.update({is_exec.group(1): result}) 
                else:
                    result = eval(command, env)
                    if inspect.isawaitable(result):
                        result = await result          

            except Exception as e:
                result = f"{type(e).__name__}: {e}"

            commands.append([
                command,
                result 
            ])

        response_str = f"```py\n" + '\n'.join([f">>> {command}\n{result}" for command, result in commands]) + "\n```"
        
        if not self.bot.user.bot:
            await ctx.message.edit(content=response_str)
        else:
            await ctx.send(response_str)

    def pull(self):
        resp = os.popen("sudo git pull").read()
        return f"```diff\n{resp}\n```"

    @commands.command(pass_context=True, name="pull", hidden=True)
    @commands.is_owner()
    async def _pull(self, ctx):
        await self._response(ctx, "Git Pull", description=self.pull(), colour=0x009688, timeout=None)

    @commands.command(pass_context=True, name="restart", hidden=True)
    @commands.is_owner()
    async def _restart(self, ctx, *, arg=None):
        if arg == "pull":
            await self._response(ctx, "Git Pull", description=self.pull(), colour=0x009688)
        await ctx.send(embed=discord.Embed(title="Restarting...", colour=0x009688))
        await self.bot.logout()

def setup(bot):
    bot.add_cog(Admin(bot))