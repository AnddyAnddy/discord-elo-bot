import discord
import matplotlib.pyplot as plt
import os
import numpy as np
from discord.ext import commands
from GAMES import GAMES
from utils.decorators import is_arg_in_modes, check_channel
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game


class Graph(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def build_wlr_graph(self, values, player):
        yList = []
        nb_wins, nb_losses = 0, 0

        for q, w, _ in values:
            if w == 1 and player in q.red_team or w == 2 and player in q.blue_team:
                nb_wins += 1
                yList.append(nb_wins / nb_losses if nb_losses != 0 else 0)
            elif w == 2 and player in q.red_team or w == 1 and player in q.blue_team:
                nb_losses += 1
                yList.append(nb_wins / nb_losses if nb_losses != 0 else 0)
        return yList

    def build_elo_graph(self, values, player):
        yList = []
        elo_running = player.elo
        for q, _, elo in values:
            # elo is positive if the red team won
            # we don't know yet in which team the player was
            if player in q.red_team:
                elo_running -= elo
                yList.append(elo_running)
            elif player in q.blue_team:
                elo_running += elo
                yList.append(elo_running)
        yList.reverse()
        return yList

    @is_arg_in_modes(GAMES)
    @commands.command(aliases=['g'])
    @check_channel('info_chat')
    async def graph(self, ctx, mode, mention="", stat_key="elo"):
        """Show the graph of previous elo points.

        This doesn't count the boosts due to double xp or win streaks.
        Name MUST be given if you want to make a graph based on the wlr.
        """
        game = get_game(ctx)
        mode = int(mode)
        player = get_player_by_mention(ctx, mode, mention) if mention\
            else get_player_by_id(ctx, mode, ctx.author.id)
        # name = str(ctx.author.id) if not name else name[3: -1]
        #
        # if not name.isdigit():
        #     await ctx.send("You better ping the player !")
        #     return
        # name = int(name)
        # if name not in game.leaderboards[mode]:
        #     await ctx.send("Couldn't find this player in the leaderboard !")
        #     return
        # player = game.leaderboards[mode][name]
        values = list(game.archive[mode].values())
        yList = []
        if stat_key == "elo":
            values.reverse()
            yList = self.build_elo_graph(values, player)
        elif stat_key == "wlr":
            yList = self.build_wlr_graph(values, player)

        xList = [x for x in range(len(yList))]

        # xList.sort()
        x = np.array(xList)
        y = np.array(yList)
        arr = np.vstack((x, y))
        plt.clf()
        plt.plot(arr[0], arr[1])
        plt.title(f'{player.name}\'s {stat_key} Graph')
        plt.xlabel("Number of games")
        plt.ylabel(f"{stat_key} points")
        plt.savefig(fname='plot')
        await ctx.send(file=discord.File('plot.png'))
        os.remove('plot.png')

    @commands.command(aliases=['oa'])
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def overall_stats(self, ctx, mode):
        """Show the number of wins of red/blue."""
        archive = get_game(ctx).archive[int(mode)]
        wins = [0, 0, 0]
        yDlist, yRlist, yBlist = [], [], []
        for _, winner, _ in archive.values():
            wins[0] += winner == 0
            wins[1] += winner == 1
            wins[2] += winner == 2
            yDlist.append(wins[0])
            yRlist.append(wins[1])
            yBlist.append(wins[2])

        total = sum(wins)

        x = np.arange(total)
        plt.clf()
        plt.plot(x, yDlist)
        plt.plot(x, yRlist)
        plt.plot(x, yBlist)
        plt.title(f'Teams wins Graph')
        plt.xlabel("Number of games")
        plt.legend(['Draw', 'Red', 'Blue'], loc='upper left')
        plt.savefig(fname='plot')
        await ctx.send(file=discord.File('plot.png'))
        os.remove('plot.png')


def setup(bot):
    bot.add_cog(Graph(bot))
