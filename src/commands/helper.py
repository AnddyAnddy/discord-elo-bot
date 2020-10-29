
from discord.ext import commands

from src.utils.utils import add_scroll
from src.utils.utils import cmds_embed


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cmds'])
    @commands.guild_only()
    async def all_commands(self, ctx):
        """Show every command."""

        msg = await ctx.send(embed=cmds_embed(self.bot))
        await add_scroll(msg)


def setup(bot):
    bot.add_cog(Helper(bot))
