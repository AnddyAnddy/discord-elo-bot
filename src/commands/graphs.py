import discord
import matplotlib.pyplot as plt
import os
import numpy as np
from discord.ext import commands
from GAMES import GAMES


class Graph(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def graph(self, ctx, mode):
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        player = game.leaderboards[mode][ctx.author.id]
        yList = []
        elo_running = player.elo
        for q, _, elo in game.archive[mode].values():
            if player in q.red_team:
                elo_running -= elo
                yList.append(elo_running)
            elif player in q.blue_team:
                elo_running += elo
                yList.append(elo_running)
        yList.reverse()
        xList = [x for x in range(len(yList))]
        # xList.sort()
        x = np.array(xList)
        y = np.array(yList)
        arr = np.vstack((x, y))
        plt.clf()
        plt.plot(arr[0], arr[1])
        plt.title(f'{ctx.message.author}\'s Elo Graph')
        plt.savefig(fname='plot')
        await ctx.send(file=discord.File('plot.png'))
        os.remove('plot.png')


def setup(bot):
    bot.add_cog(Graph(bot))
