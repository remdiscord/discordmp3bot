#! /usr/bin/env python

"""
mp3bot ~ bot.py
Discord Bot

Copyright (c) 2017 Joshua Butt
"""
import asyncio
import logging

import discord
from discord.ext import commands

from config import *


bot_config = {
    'command_prefix': commands.when_mentioned_or(COMMAND_PREFIX),
    'pm_help': False,
    'self_bot': IS_SELFBOT,
    'status': discord.Status.online,
    'owner_id': OWNER_ID,
    'fetch_offline_members': False
}
bot = commands.Bot(**bot_config)

bot.log = logging.getLogger()
bot.log.setLevel(logging.INFO if DEBUG else logging.WARNING)
handler = logging.FileHandler(filename=f"{APP_NAME}.log")
formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{")
handler.setFormatter(formatter)
bot.log.addHandler(handler)
bot.log.info("Instance started.")

@bot.event
async def on_ready():
    bot.owner = discord.utils.get(bot.get_all_members(), id=bot.owner_id)
    bot.log.info(f"Bot {bot.user} started!")

    # Set game to help prefix
    await bot.change_presence(game=discord.Game(name=f"{bot.command_prefix(bot, None)[0]}help"))

    print(f"""#--------------------------------------#
| Succesfully logged in as {bot.user}
# -------------------------------------#
| Username: {bot.user.name}
| User ID: {bot.user.id}
| Owner: {bot.owner}
| Guilds: {len(bot.guilds)}
# -------------------------------------#""")

if __name__ == "__main__":
    for cog in INITIAL_COGS:
        try:
            bot.load_extension(cog)
            bot.log.info(f"Succesfully loaded extension: {cog}")
        except Exception as e:
            error = f"Failed to load extension: {cog}\n{type(e).__name__}: {e}"
            bot.log.error(error)
            print(error)

    bot.run(TOKEN, bot=not IS_SELFBOT)

    raise Exception("Bot Restarting...")