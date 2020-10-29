import os

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

from src.utils.decorators import is_arg_in_modes, check_channel
from src.utils.exceptions import get_game
from src.utils.exceptions import get_player_by_id, get_player_by_mention


class Graph(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def build_wlr_graph(values, player):
        y_list = []
        nb_wins, nb_losses = 0, 0

        for q, w, _ in values:
            if w == 1 and player in q.red_team or w == 2 and player in q.blue_team:
                nb_wins += 1
                y_list.append(nb_wins / nb_losses if nb_losses != 0 else 0)
            elif w == 2 and player in q.red_team or w == 1 and player in q.blue_team:
                nb_losses += 1
                y_list.append(nb_wins / nb_losses if nb_losses != 0 else 0)
        return y_list

    @staticmethod
    def build_elo_graph(values, player):
        y_list = []
        elo_running = player.elo
        for q, _, elo in values:
            # elo is positive if the red team won
            # we don't know yet in which team the player was
            if player in q.red_team:
                elo_running -= elo
                y_list.append(elo_running)
            elif player in q.blue_team:
                elo_running += elo
                y_list.append(elo_running)
        y_list.reverse()
        return y_list

    @is_arg_in_modes()
    @commands.command(aliases=['g'])
    @check_channel('info_chat')
    @commands.guild_only()
    async def graph(self, ctx, mode, mention="", stat_key="elo"):
        """Show the graph of previous elo points.

        This doesn't count the boosts due to double xp or win streaks.
        Name MUST be given if you want to make a graph based on the wlr.
        """
        game = get_game(ctx)
        player = await get_player_by_mention(ctx, mode, mention) if mention\
            else await get_player_by_id(ctx, mode, ctx.author.id)
        values = list(game.archive[mode].values())
        y_list = []
        if stat_key == "elo":
            values.reverse()
            y_list = self.build_elo_graph(values, player)
        elif stat_key == "wlr":
            y_list = self.build_wlr_graph(values, player)

        x_list = [x for x in range(len(y_list))]

        x = np.array(x_list)
        y = np.array(y_list)
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
    @is_arg_in_modes()
    @commands.guild_only()
    async def overall_stats(self, ctx, mode):
        """Show the number of wins of red/blue."""
        archive = get_game(ctx).archive[mode]
        wins = [0, 0, 0]
        y_dlist, y_rlist, y_blist = [], [], []
        for _, winner, _ in archive.values():
            wins[0] += winner == 0
            wins[1] += winner == 1
            wins[2] += winner == 2
            y_dlist.append(wins[0])
            y_rlist.append(wins[1])
            y_blist.append(wins[2])

        total = sum(wins)

        x = np.arange(total)
        plt.clf()
        plt.plot(x, y_dlist)
        plt.plot(x, y_rlist)
        plt.plot(x, y_blist)
        plt.title(f'Teams wins Graph')
        plt.xlabel("Number of games")
        plt.legend(['Draw', 'Red', 'Blue'], loc='upper left')
        plt.savefig(fname='plot')
        await ctx.send(file=discord.File('plot.png'))
        os.remove('plot.png')


def setup(bot):
    bot.add_cog(Graph(bot))
