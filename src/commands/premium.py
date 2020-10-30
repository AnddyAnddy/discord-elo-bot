import time

import discord
import math
from discord import Embed
from discord.ext import commands

from main import DISCORD_MAIN_GUILD_ID
from src.utils.decorators import check_channel
from src.utils.exceptions import get_game


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium_in_main_server(self, id_author):
        try:
            guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
            player = guild.get_member(id_author)
            role = discord.utils.get(guild.roles, name="waiting for premium")
            return player is not None and role in player.roles
        except Exception:  # Any user wanting to cheat on their own "waiting for premium" role
            return False

    @staticmethod
    async def set_premium(ctx):
        game = get_game(ctx)
        game.limit_leaderboards = math.inf
        time_to_add = 60 * 60 * 24 * 30
        if game.date_premium_end == 0:
            game.date_premium_end = time.time() + time_to_add
            print(time.time(), game.date_premium_end)
        else:
            game.date_premium_end += time_to_add
        await ctx.send(embed=Embed(color=0x00FF00,
                                   title="Thanks for supporting me !",
                                   description=f"You got your unlimited amount of player for every mode !\n"
                                               "Any issue ? Ping Anddy#2086 on the main server !."
                                   )
                       )

    async def remove_role(self, id_author):
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        role = discord.utils.get(guild.roles, name="waiting for premium")
        await player.remove_roles(role)

    @commands.command()
    @check_channel('register')
    @commands.guild_only()
    async def premium(self, ctx):
        """Claim your premium after supporting on patreon.

        After getting the wanted premium role on the main server,
        go on #premium channel in your server and write !premium
        """
        id = ctx.author.id
        if not self.is_premium_in_main_server(id):
            await ctx.send(embed=Embed(color=0x000000,
                                       description="You are not waiting for premium in the main server "
                                                   "https://discord.gg/E2ZBNSx!\n "
                                                   "Make sure you linked your discord with patreon."))
            return
        await self.set_premium(ctx)
        await self.remove_role(id)


def setup(bot):
    bot.add_cog(Premium(bot))
