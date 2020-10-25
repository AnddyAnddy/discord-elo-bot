import discord
from discord import Embed
from discord.ext import commands
from main import GAMES, DISCORD_MAIN_GUILD_ID
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game
from utils.decorators import check_channel


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium_in_main_server(self, id_author):
        print(type(id_author))
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        role = discord.utils.get(guild.roles, name="waiting for premium")
        print(guild, id_author, player, role)
        return player is not None and role in player.roles



    async def set_premium(self, ctx, id):
        game = get_game(ctx)
        game.limit_leaderboards = 0xFFFFFF
        await ctx.send(embed=Embed(color=0x00FF00,
            title="Thanks for supporting me !",
            description=\
                f"You got your unlimited amount of player for every mode !\n"\
                "Any issue ? Ping Anddy#2086 on the main server !."
            )
        )


    async def remove_role(self, id_author):
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        role = discord.utils.get(guild.roles, name="waiting for premium")
        await player.remove_roles(role)

    @commands.command()
    async def test(self, ctx):
        id = ctx.author.id
        print(await ctx.guild.chunk())


    @commands.command()
    @check_channel('register')
    async def premium(self, ctx):
        """Claim your premium after supporting on patreon.

        After getting the wanted premium role on the main server,
        go on #premium channel in your server and write !premium
        """
        id = ctx.author.id
        if not self.is_premium_in_main_server(id):
            await ctx.send(embed=Embed(color=0x000000,
                description="You are not waiting for premium in the main server! "\
                    "Make sure you linked your discord with patreon."))
            return
        await self.set_premium(ctx, id)
        await self.remove_role(id)

def setup(bot):
    bot.add_cog(Premium(bot))
