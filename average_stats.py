class AverageStats:
    def __init__(self, average_kills, average_deaths, average_kd, average_kr, average_hs, winrate, real_kd, passed, amount_of_games, highest_elo, lowest_elo):
        self.averageKills = average_kills
        self.averageDeaths = average_deaths
        self.averageKD = average_kd
        self.averageKR = average_kr
        self.averageHS = average_hs
        self.winRate = winrate
        self.realKD = real_kd
        self.passed = passed
        self.amountOfGames = amount_of_games
        self.highestELO = highest_elo
        self.lowestELO = lowest_elo

    def __str__(self):
        return "Average kills: {}, Average deaths: {}, Average KD: {}, Average KR: {}, Average HS: {}, Winrate: {}, Real KD: {}, Passed: {}, Matches: {}, Highest Elo: {}, Lowest Elo: {}".\
            format(self.averageKills, self.averageDeaths, self.averageKD, self.averageKR, self.averageHS, self.winRate, self.realKD, self.passed, self.amountOfGames, self.highestELO, self.lowestELO)
