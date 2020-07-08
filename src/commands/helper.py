
from discord import Embed
from discord.ext import commands
from main import GAMES



class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cmds_embed(self, startpage=1):
        nb_pages = 1 + len(self.bot.commands) // 15
        nl = '\n'
        return Embed(color=0x00FF00, description=\
              '```\n' +\
             '\n'.join([f'{command.name:15}: {command.help.split(nl)[0]}'
                for command in sorted(self.bot.commands, key=lambda c: c.name)[15 * (startpage - 1): 15 * startpage]
                if command.help is not None and not command.hidden]) + '```')\
                .add_field(name="name", value="commands") \
                .add_field(name="-", value="-") \
                .add_field(name="-", value=0) \
                .set_footer(text=f"[ {startpage} / {nb_pages} ]")


    @commands.command(aliases=['cmds'])
    async def all_commands(self, ctx):
        """Show every command."""

        msg = await ctx.send(embed=self.cmds_embed())
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")


def setup(bot):
    bot.add_cog(Helper(bot))
