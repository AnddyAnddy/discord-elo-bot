
from discord import Embed
from discord.ext import commands
from main import GAMES
from utils.utils import cmds_embed
from utils.utils import add_scroll


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cmds'])
    async def all_commands(self, ctx):
        """Show every command."""

        msg = await ctx.send(embed=cmds_embed(self.bot))
        await add_scroll(msg)


def setup(bot):
    bot.add_cog(Helper(bot))
