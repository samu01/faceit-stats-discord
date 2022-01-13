import os
import discord

from discord.ext.commands import Bot
from helpers import puts

TOKEN = os.environ.get('DISCORD_TOKEN')

last_cmd_times = {}

bot = Bot(command_prefix='-',
          command_attrs=dict(hidden=True))
bot.remove_command("help")

puts(f"[Info] discord.py v{discord.__version__}")

@bot.event
async def on_message(message):
    if not bot.is_ready() or message.author.bot:
        return

    await bot.process_commands(message)

@bot.event
async def on_ready():
    puts('[Info] Logged in as: {0.user.name} ({0.user.id})'.format(bot))
    puts(f'[Info] Connected to {str(len(bot.guilds))} servers.')
    for x in range(len(bot.guilds)):
        puts(f'[Info] {x+1}. {bot.guilds[x].name}')

    await bot.change_presence(activity=discord.Game(name='-help'))

@bot.event
async def on_guild_join(guild):
    puts(f'[Info] Joined a server: {guild}')
    puts(f'[Info] Now connected to {str(len(bot.guilds))}')
    for x in range(len(bot.guilds)):
        puts(f'[Info] {x + 1}. {bot.guilds[x].name}')

bot.load_extension("cogs.Faceit")

puts("[Info] Starting bot")
bot.run(TOKEN)
