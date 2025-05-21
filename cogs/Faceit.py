import os
import json
import traceback
import sys
import re

import random
import asyncio

import discord

from faceit_api.faceit_data import FaceitData

from discord.ext import commands
from helpers import puts, elo_to_next_level, get_average_stats_of_last_x_matches, get_emoji_level, fetch_steam_id_by_vanity_url

FC_TOKEN = os.environ.get('FACEIT_TOKEN')

faceit_data = FaceitData(FC_TOKEN)

class Faceit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x0069a4

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def faceit(self, ctx: commands.Context, nickname: str):
        faceit_name = nickname

        steamid64 = None
        if faceit_name.startswith("765"):
            steamid64 = faceit_name

        steam_id64_match = re.search(r"steamcommunity.com\/profiles\/([A-Za-z_0-9]+)", faceit_name)
        if steam_id64_match:
            steamid64 = steam_id64_match.group(1)
        else:
            steam_id64_match = re.search(r"steamcommunity.com\/id\/([A-Za-z_0-9]+)", faceit_name)
            if steam_id64_match:
                steamid64 = fetch_steam_id_by_vanity_url(steam_id64_match.group(1))

        if steamid64 is not None:
            puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up stats for {steamid64}")
            message = await ctx.send(f"> Looking up stats for **{steamid64}**")

            player = faceit_data.player_details(game="cs2", game_player_id=steamid64)
            if player is None:
                return await message.edit(content=f"{message.content}\n> Couldn't find a player with steamid \"{steamid64}\"")
            else:
                player_id = player["player_id"]
        else:    
            puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up stats for {faceit_name}")
            message = await ctx.send(f"> Looking up stats for **{faceit_name}**")

            player = faceit_data.player_details(faceit_name, "cs2")
            if player is None or "nickname" not in player:
                puts(f"[Info] {ctx.author}: Name ({faceit_name} not exact, searching...")
                await message.edit(content=f"{message.content}\n> Name not exact, searching...")

                player_search = faceit_data.search_players(faceit_name, "cs2", None, 0, 1)
                items = player_search['items']
                if len(items) == 0:
                    return await message.edit(content=f"{message.content}\n> Couldn't find a player with the name \"{nickname}\"")

                player_id = player_search['items'][0]["player_id"]
            else:
                player_id = player["player_id"]

        if player is None:
            player = faceit_data.player_id_details(player_id)

        if player is None:
            return await message.edit(content=f"{message.content}\n> Couldn't find a player with the name \"{nickname}\"")

        if "cs2" not in player["games"]:
            return await message.edit(content=f"{message.content}\n> {nickname} has not played cs2")

        player_csgo_stats = faceit_data.player_stats(player_id, "cs2")
        
        player_name = player["nickname"]
        player_faceit_url = player["faceit_url"].replace("{lang}", "en")
        player_avatar = player["avatar"]
        #player_afk_infractions = player["infractions"]["afk"]
        #player_leaver_infractions = player["infractions"]["leaver"]
        player_csgo_elo = player["games"]["cs2"]["faceit_elo"]
        player_csgo_level = player["games"]["cs2"]["skill_level"]
        player_lifetime_averagekd = player_csgo_stats["lifetime"]["Average K/D Ratio"]
        player_lifetime_winrate = player_csgo_stats["lifetime"]["Win Rate %"]
        player_lifetime_averagehs = player_csgo_stats["lifetime"]["Average Headshots %"]
        player_lifetime_longestwinstreak = player_csgo_stats["lifetime"]["Longest Win Streak"]
        player_lifetime_currentwinstreak = player_csgo_stats["lifetime"]["Current Win Streak"]
        player_lifetime_matches = player_csgo_stats["lifetime"]["Matches"]

        player_elo_to_next_level = elo_to_next_level(player_csgo_elo, player_csgo_level)
        player_elo_to_next_level_msg = f"({player_elo_to_next_level} to next level)"
        if player_elo_to_next_level == -1:
            player_elo_to_next_level_msg = ""
        
        #player_reg_status = "unknown"
        #player_details_v1 = faceit_data.player_details_v1_api(player_name)
        #if player_details_v1 is not None:
        #    if "result" in player_details_v1:
        #        if "ok" in player_details_v1["result"]:
        #            player_reg_status = player_details_v1["payload"]["registration_status"]

        level_emoji = get_emoji_level(player_csgo_level)

        emb = discord.Embed(color=self.color, url=player_faceit_url, title=player_name)
        emb.set_footer(text=f"Stats for {player_name}", icon_url=player_avatar)
        emb.set_thumbnail(url=player_avatar)
        emb.add_field(name="Level", value=f"{level_emoji}")
        emb.add_field(name="ELO", value=f"{player_csgo_elo} {player_elo_to_next_level_msg}")
        emb.add_field(name="Matches", value=f"{player_lifetime_matches}", inline=False)
        emb.add_field(name="Longest Win Streak", value=f"{player_lifetime_longestwinstreak}", inline=False)
        emb.add_field(name="Current Win Streak", value=f"{player_lifetime_currentwinstreak}", inline=False)
        emb.add_field(name="Win rate", value=f"{player_lifetime_winrate}%", inline=False)
        emb.add_field(name="Average K/D", value=f"{player_lifetime_averagekd}", inline=False)
        emb.add_field(name="Average HS", value=f"{player_lifetime_averagehs}%", inline=False)
        #emb.add_field(name="Leaver Infractions", value=f"{player_leaver_infractions}", inline=False)
        #emb.add_field(name="AFK Infractions", value=f"{player_afk_infractions}", inline=False)
        #emb.add_field(name="Account Status", value=f"{player_reg_status}", inline=False)
        await message.edit(content="", embed=emb)
        
    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def elo(self, ctx: commands.Context, nickname: str, nickname2: str = "", nickname3: str = "", nickname4: str = "", nickname5: str = ""):
        faceit_names = [nickname, nickname2, nickname3, nickname4, nickname5]
        faceit_elos = [0, 0, 0, 0, 0]
        
        names = ""
        for name in faceit_names:
            if name == "":
                continue
            
            if names == "":
                names = name
            else:
                names = f"{names}, {name}"
        
        counter = 0
        emb = discord.Embed(color=self.color)
        emb.add_field(name="Looking up players", value=f"{names}\n‌")
        message = await ctx.send(embed=emb)
        
        for faceit_name in faceit_names:
            if faceit_name == "":
                continue
            
            eloregex = re.findall(r'elo:(\d+)', faceit_name)
            if eloregex:
                emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\n{faceit_name}: **{eloregex[0]}**")
                await message.edit(embed=emb)
            
                faceit_elos[counter] = int(eloregex[0])
                counter += 1
                continue
        
            puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up elo of {faceit_name}")

            player = faceit_data.player_details(faceit_name, "cs2")
            if player is None or "nickname" not in player:
                puts(f"[Info] {ctx.author}: Name ({faceit_name} not exact, searching...")
                
                emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\nName not exact, searching...")
                await message.edit(embed=emb)

                player_search = faceit_data.search_players(faceit_name, "cs2", None, 0, 1)
                items = player_search['items']
                if len(items) == 0:
                    emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\nCouldn't find a player with the name \"{faceit_name}\"")
                    return await message.edit(embed=emb)
                    
                player_id = player_search['items'][0]["player_id"]
            else:
                player_id = player["player_id"]

            if player is None:
                player = faceit_data.player_id_details(player_id)

            if player is None:
                emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\nCouldn't find a player with the name \"{faceit_name}\"")
                return await message.edit(embed=emb)

            if "cs2" not in player["games"]:
                emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\n{faceit_name} has not played cs2")
                return await message.edit(embed=emb)

            player_csgo_stats = faceit_data.player_stats(player_id, "cs2")

            player_name = player["nickname"]
            player_csgo_elo = player["games"]["cs2"]["faceit_elo"]
            
            emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\n{player_name}: **{player_csgo_elo}**")
            await message.edit(embed=emb)
            
            faceit_elos[counter] = int(player_csgo_elo)
            counter += 1
            
        
        added_up_elos = 0
        for faceit_elo in faceit_elos:
            added_up_elos += faceit_elo
        
        average_elos = int(added_up_elos / counter)
        puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} Average elo: {average_elos}")
        emb.set_field_at(0, name="Looking up players", value=f"{emb.fields[0].value}\nAverage Elo: **{average_elos}**")
        await message.edit(embed=emb)
        
    @elo.error
    async def elo_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send('> zzzzzzz...')

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'> {self.bot.command_prefix}elo <nickname> [nickname2] [nickname3] [nickname4] [nickname5]')

        # puts(error)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send('> something went wrong')

    @faceit.error
    async def faceit_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send('> zzzzzzz...')

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'> {self.bot.command_prefix}faceit <nickname>')

        # puts(error)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send('> something went wrong')

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def average(self, ctx: commands.Context, nickname: str, amount_of_games: int = 20, ignore_1v1s: bool = True):
        if amount_of_games <= 0:
            return await ctx.send("Amount of games can't be less than 1")

        faceit_name = nickname

        puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up {amount_of_games} match averages for {faceit_name}")

        steamid64 = None

        steam_id64_match = re.search(r"steamcommunity.com\/profiles\/([A-Za-z_0-9]+)", faceit_name)
        if steam_id64_match:
            steamid64 = steam_id64_match.group(1)
        else:
            steam_id64_match = re.search(r"steamcommunity.com\/id\/([A-Za-z_0-9]+)", faceit_name)
            if steam_id64_match:
                steamid64 = await fetch_steam_id_by_vanity_url(steam_id64_match.group(1))

        if steamid64 is not None:
            puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up stats for {steamid64}")
            message = await ctx.send(f"> Looking up stats for **{steamid64}**")

            player_d = faceit_data.player_details(game="cs2", game_player_id=steamid64)
            if player_d is None:
                return await message.edit(content=f"{message.content}\n> Couldn't find a player with steamid \"{steamid64}\"")
            else:
                player_id = player_d["player_id"]
        else:
            puts(f"[Info] [{ctx.guild}: {ctx.channel}] {ctx.author} looking up stats for {faceit_name}")
            message = await ctx.send(f"> Looking up stats for **{faceit_name}**")

            player_d = faceit_data.player_details(faceit_name, "cs2")
            if player_d is None or "nickname" not in player_d:
                puts(f"[Info] {ctx.author}: Name ({faceit_name} not exact, searching...")
                await message.edit(content=f"{message.content}\n> Name not exact, searching...")

                player_search = faceit_data.search_players(faceit_name, "cs2", None, 0, 1)
                items = player_search['items']
                if len(items) == 0:
                    return await message.edit(content=f"{message.content}\n> Couldn't find a player with the name \"{nickname}\"")

                player_id = player_search['items'][0]["player_id"]
            else:
                player_id = player_d["player_id"]

        if player_d is None:
            player_d = faceit_data.player_id_details(player_id)

        if player_d is None:
            return await message.edit(content=f"{message.content}\n> Couldn't find a player with the name \"{nickname}\"")

        if "cs2" not in player_d["games"]:
            return await message.edit(content=f"{message.content}\n> {nickname} has not played cs2")

        player_name = player_d["nickname"]
        player_faceit_url = player_d["faceit_url"].replace("{lang}", "en")
        player_avatar = player_d["avatar"]
        player_csgo_level = player_d["games"]["cs2"]["skill_level"]
        level_emoji = get_emoji_level(player_csgo_level)

        player_last_x_average_stats = get_average_stats_of_last_x_matches(faceit_data, player_id, amount_of_games, ignore_1v1s)
        
        if player_last_x_average_stats.amountOfGames == -1:
            return await message.edit(content=f"{message.content}\n> No matches found for {nickname}")

        emb2 = discord.Embed(color=self.color, url=player_faceit_url, title=f"{level_emoji} {player_name}")
        emb2.set_footer(text=f"Average stats from {player_last_x_average_stats.amountOfGames} matches", icon_url=player_avatar)
        emb2.add_field(name="Average Kills", value=f"{player_last_x_average_stats.averageKills}", inline=False)
        emb2.add_field(name="Average Deaths", value=f"{player_last_x_average_stats.averageDeaths}", inline=False)
        emb2.add_field(name="Average K/D", value=f"{player_last_x_average_stats.averageKD}", inline=True)
        emb2.add_field(name="Real K/D", value=f"{player_last_x_average_stats.realKD}", inline=True)
        emb2.add_field(name="Average K/R", value=f"{player_last_x_average_stats.averageKR}", inline=False)
        emb2.add_field(name="Average HS", value=f"{player_last_x_average_stats.averageHS}%", inline=False)
        emb2.add_field(name="Win rate", value=f"{player_last_x_average_stats.winRate}%", inline=False)
        #emb2.add_field(name="Highest ELO", value=f"{player_last_x_average_stats.highestELO}", inline=True)
        #emb2.add_field(name="Lowest ELO", value=f"{player_last_x_average_stats.lowestELO}", inline=True)
        await message.edit(content="", embed=emb2)

        if player_last_x_average_stats.passed != 0:
            if player_last_x_average_stats.passed != 1:
                await ctx.send(f"Ignored {player_last_x_average_stats.passed} matches that were not 5v5.")
            else:
                await ctx.send(f"Ignored {player_last_x_average_stats.passed} match that was not 5v5.")

    @average.error
    async def average_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send('> zzzzzzz...')

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'> {self.bot.command_prefix}average <nickname> <amount_of_games> [ignore_1v1s]')

        # puts(error)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send('> something went wrong')


def setup(bot):
    bot.add_cog(Faceit(bot))
