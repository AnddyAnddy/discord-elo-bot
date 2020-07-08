from discord import Embed
from main import GAMES
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from utils.decorators import check_category, check_channel, is_arg_in_modes


class Match_process(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['s', 'game'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def submit(self, ctx, mode, id_game, winner):
        """Submit the score of a game.

        Example: !s 1 7 1
        in the mode 1vs1, in the 7th game, the team 1 (red) won.
        This will update the rankings.
        """
        game = GAMES[ctx.guild.id]
        if not id_game.isdigit() or not winner.isdigit():
            raise commands.errors.MissingRequiredArgument
        mode, id_game, winner = int(mode), int(id_game), int(winner)
        await ctx.send(embed=Embed(color=0xFF0000 if winner == 1 else 0x0000FF,
                                   description=game.add_archive(mode, id_game, winner)))

    @commands.command()
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def undo(self, ctx, mode, id_game):
        """Undo a game.

        Example: !undo 1 7
        in the mode 1vs1, in the 7th game.
        This will reset the ranking updates of this match.
        The game will be in undecided.
        """
        game = GAMES[ctx.guild.id]
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.undo(int(mode), int(id_game))))

    @commands.command(aliases=['c', 'clear'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def cancel(self, ctx, mode, id_game):
        """Cancel the game given in arg.

        Example: !cancel 1 3
        will cancel the game with the id 3 in the mode 1vs1.
        """
        game = GAMES[ctx.guild.id]
        if game.cancel(int(mode), int(id_game)):
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"The game {id_game} has been canceled"))
        else:
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"Couldn't find the game {id_game} in the current games."))

    @commands.command(aliases=['uc', 'uclear'])
    @has_permissions(manage_roles=True)
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def uncancel(self, ctx, mode, id_game):
        """Uncancel the game given in arg.

        Example: !uncancel 1 3
        will uncancel the game with the id 3 in the mode 1vs1.
        """
        game = GAMES[ctx.guild.id]
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.uncancel(int(mode), int(id_game))))

    @commands.command(aliases=['u'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def undecided(self, ctx, mode):
        """Display every undecided games.

        Example: !undecided 2
        Will show every undecided games in 2vs2, with the format below.
        id: [id], Red team: [player1, player2], Blue team: [player3, player4]."""
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.undecided(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")

    @commands.command(aliases=['cl'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def canceled(self, ctx, mode):
        """Display every canceled games of a specific mode.

        Example: !cl 2
        Will show every canceled games in 2vs2.
        """
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.canceled(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")

    @commands.command(aliases=['a'])
    @check_category('Elo by Anddy')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def archived(self, ctx, mode):
        """Display every games of a specific mode.

        Example: !archived 2
        Will show every games in 2vs2, with the format below.
        id: [id], Winner: Team Red/Blue, Red team: [player1, player2],
        Blue team: [player3, player4]."""
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.archived(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")


def setup(bot):
    bot.add_cog(Match_process(bot))
