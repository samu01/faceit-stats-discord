import time
import requests
import json
from faceit_api.faceit_data import FaceitData
from average_stats import AverageStats
from datetime import datetime


def current_milli_time():
    return int(round(time.time() * 1000))


def puts(text):
    # Print message to console
    message = '[' + str(datetime.now()) + ']$ ' + str(text)
    print(message)


def get_level_from_elo(current_elo):
    if 1 < current_elo <= 800:
        return 1
    if 801 < current_elo <= 950:
        return 2
    if 951 < current_elo <= 1100:
        return 3
    if 1101 < current_elo <= 1250:
        return 4
    if 1251 < current_elo <= 1400:
        return 5
    if 1400 < current_elo <= 1550:
        return 6
    if 1551 < current_elo <= 1700:
        return 7
    if 1701 < current_elo <= 1850:
        return 8
    if 1851 < current_elo <= 2000:
        return 9
    if 2001 < current_elo:
        return 10


def get_emoji_level(level: int):
    if level == 1:
        return "<:skill_level_1:674691164644835358>"
    elif level == 2:
        return "<:skill_level_2:674691164552822790>"
    elif level == 3:
        return "<:skill_level_3:674691164598698024>"
    elif level == 4:
        return "<:skill_level_4:674691164439314446>"
    elif level == 5:
        return "<:skill_level_5:674691589838471188>"
    elif level == 6:
        return "<:skill_level_6:674691164615475231>"
    elif level == 7:
        return "<:skill_level_7:674691164267347999>"
    elif level == 8:
        return "<:skill_level_8:674691164598829056>"
    elif level == 9:
        return "<:skill_level_9:674691164636577798>"
    elif level == 10:
        return "<:skill_level_10:674691164674457610>"


def get_level_max_elo(level: int):
    max_elos = {
        0: 0,
        1: 800,
        2: 950,
        3: 1100,
        4: 1250,
        5: 1400,
        6: 1550,
        7: 1700,
        8: 1850,
        9: 2000,
    }
    return max_elos.get(level)


def elo_to_next_level(current_elo: int, current_level: int):
    if current_elo is None or current_level is None:
        return
    if current_level == 10:
        return -1

    max_elo = get_level_max_elo(current_level)
    return max_elo - current_elo + 1


def get_average_stats_of_last_x_matches(faceit_data: FaceitData, player_id: str, amount: int, ignore_1v1s: bool) -> AverageStats:
    #player_matches = faceit_data.player_matches_v1_api(player_id, "cs2", amount)
    player_matches = faceit_data.player_matches(player_id, "cs2", None, None, 0, amount)
    if len(player_matches["items"]) == 0:
        return AverageStats(-1, -1, -1, -1, -1, -1, -1, 0, -1, -1, -1)
        
    matches = 0
    passed = 0

    total_kills = 0
    total_deaths = 0
    total_kd = 0
    total_kr = 0
    total_hs = 0
    total_wins = 0
    lowest_elo = 9999
    highest_elo = 0
    
    for player_match in player_matches["items"]:
        player_match_stats = faceit_data.match_stats(player_match["match_id"])
        for match_round in player_match_stats["rounds"]:
            if ignore_1v1s and "5v5" not in match_round["game_mode"]:
                passed += 1
                continue
        
            player_stats = None
            for team in match_round["teams"]:
                for player in team["players"]:
                    if player["player_id"] == player_id:
                        player_stats = player["player_stats"]
                        break
                        
            if player_stats is not None:
                matches += 1
                total_kills += int(player_stats["Kills"])
                total_deaths += int(player_stats["Deaths"])
                total_kd += float(player_stats["K/D Ratio"])
                total_kr += float(player_stats["K/R Ratio"])
                total_hs += int(player_stats["Headshots %"])
                if int(player_stats["Result"]) == 1:
                    total_wins += 1
    
    #for player_match in player_matches:
    #    if ignore_1v1s and "5v5" not in player_match["gameMode"]:
    #        passed += 1
    #        continue

    #    total_kills += int(player_match["i6"])
    #    total_deaths += int(player_match["i8"])
    #    total_kd += float(player_match["c2"])
    #    total_kr += float(player_match["c3"])
    #    total_hs += int(player_match["c4"])
    #    if "elo" in player_match:
    #        elo = int(player_match["elo"])
    #        if elo > highest_elo:
    #            highest_elo = elo
    #        if elo < lowest_elo:
    #            lowest_elo = elo

    #    if player_match["i2"] == player_match["teamId"]:
    #        total_wins += 1

    #matches = len(player_matches["items"]) - passed
    average_kills = round(total_kills / matches, 1)
    average_deaths = round(total_deaths / matches, 1)
    average_kd = round(total_kd / matches, 2)
    average_kr = round(total_kr / matches, 2)
    average_hs = round(total_hs / matches)
    winrate = round((total_wins / matches) * 100)
    real_kd = round(total_kills / total_deaths, 2)
    average_stats = AverageStats(average_kills, average_deaths, average_kd, average_kr, average_hs, winrate, real_kd, passed, matches, highest_elo, lowest_elo)
    puts(average_stats)
    return average_stats
