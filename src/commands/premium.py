import discord
from discord import Embed
from discord.ext import commands
from main import GAMES, DISCORD_MAIN_GUILD_ID
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium_in_main_server(self, id_author):
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        role = discord.utils.get(guild.roles, name="waiting for premium")
        return player is not None and role in player.roles


    def get_premium_nb_games(self, id_author):
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        for role in player.roles:
            if "double" in role.name:
                return int(role.name.split()[0])

        return 0

    async def set_premium(self, ctx, id):
        game = get_game(ctx)
        nb_games = self.get_premium_nb_games(id)
        for mode in game.available_modes:
            if id in game.leaderboards[mode]:
                game.leaderboards[mode][id].double_xp += nb_games
        await ctx.send(embed=Embed(color=0x00FF00,
            title="Thanks for supporting me !",
            description=\
                f"You got your {nb_games} double xp available on every mode "\
                "you registered in, check !info <mode> to be sure.\n"\
                "Any issue ? Ping Anddy#2086 on the main server !."
            )
        )


    async def remove_role(self, id_author):
        guild = discord.utils.get(self.bot.guilds, id=DISCORD_MAIN_GUILD_ID)
        player = guild.get_member(id_author)
        role = discord.utils.get(guild.roles, name="waiting for premium")
        await player.remove_roles(role)


    @commands.command()
    async def premium(self, ctx):
        """Claim your premium after supporting on patreon.

        After getting the wanted premium role on the main server,
        go on #premium channel in your server and write !premium
        to be sure you earned the premium, check your own stats
        and your remaining premium games are in the "double_xp" stat.
        """
        id = ctx.author.id
        if not self.is_premium_in_main_server(id):
            await ctx.send("You are not waiting for premium in the main server !"\
                "Be sure that you linked your discord with patreon.")
            return
        await self.set_premium(ctx, id)
        await self.remove_role(id)

def setup(bot):
    bot.add_cog(Premium(bot))
