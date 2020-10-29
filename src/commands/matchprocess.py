from discord import Embed
from discord.ext import commands

from main import GAMES
from src.utils.decorators import check_channel, is_arg_in_modes, has_role_or_above
from src.utils.exceptions import get_game
from src.utils.utils import add_scroll
from src.utils.utils import auto_submit_reactions, map_pick_reactions


class MatchProcess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_reaction_add(self, reaction, user):
        """

        @param user: discord.User
        @type reaction: discord.Reaction
        """
        reaction.emoji = str(reaction)
        if user.id == self.bot.user.id or not reaction.message.embeds:
            return
        game = GAMES[user.guild.id]
        # if reaction.emoji in "✅❌":
        # red, blue, draw, cancel
        if reaction.emoji in "🟢🔴🔵❌":
            await auto_submit_reactions(reaction, user, game)
            return
        if reaction.emoji in game.available_maps.values():
            await map_pick_reactions(reaction, user, game)
            return

        if reaction.emoji in "👍👎":
            return
        await reaction.message.remove_reaction(reaction.emoji, user)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_reaction_remove(self, reaction, user):
        if user.id == self.bot.user.id or not reaction.message.embeds:
            return
        game = GAMES[user.guild.id]
        # red, blue, draw, cancel
        if reaction.emoji in "🟢🔴🔵❌":
            await auto_submit_reactions(reaction, user, game, True)

    @commands.command(aliases=['s', 'game'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def submit(self, ctx, mode, id_game, winner):
        """Submit the score of a game.

        Example: !s 1 7 1
        in the mode 1vs1, in the 7th game, the team 1 (red) won.
        This will update the rankings.
        """
        game = get_game(ctx)
        if not id_game.isdigit() or not winner.isdigit():
            raise commands.errors.MissingRequiredArgument(id_game)
        id_game, winner = int(id_game), int(winner)
        text, worked = game.add_archive(mode, id_game, winner)
        await ctx.send(embed=Embed(color=0xFF0000 if winner == 1 else 0x0000FF,
                                   description=text))
        if worked and mode in game.waiting_for_approval:
            game.waiting_for_approval[mode].pop(id_game, None)

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def undo(self, ctx, mode, id_game):
        """Undo a game.

        Example: !undo 1 7
        in the mode 1vs1, in the 7th game.
        This will reset the ranking updates of this match.
        The game will be in embed_undecided.
        """
        game = get_game(ctx)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.undo(mode, int(id_game))))

    @commands.command(aliases=['c', 'clear'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def cancel(self, ctx, mode, id_game):
        """Cancel the game given in arg.

        Example: !cancel 1 3
        will cancel the game with the id 3 in the mode 1vs1.
        """
        game = get_game(ctx)
        if game.cancel(mode, int(id_game)):
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"The game {id_game} has been embed_canceled"))
        else:
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"Could not find the game {id_game} in the current games."))

    @commands.command(aliases=['uc'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def uncancel(self, ctx, mode, id_game):
        """Uncancel the game given in arg.

        Example: !uncancel 1 3
        will uncancel the game with the id 3 in the mode 1vs1.
        """
        game = get_game(ctx)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=game.uncancel(mode, int(id_game))))

    @commands.command(aliases=['u'])
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def undecided(self, ctx, mode):
        """Display every embed_undecided games.

        Example: !embed_undecided 2
        Will show every embed_undecided games in 2vs2, with the format below.
        id: [id], Red team: [player1, player2], Blue team: [player3, player4]."""
        game = get_game(ctx)
        msg = await ctx.send(embed=game.embed_undecided(mode))
        await add_scroll(msg)

    @commands.command(aliases=['cl'])
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def canceled(self, ctx, mode):
        """Display every embed_canceled games of a specific mode.

        Example: !cl 2
        Will show every embed_canceled games in 2vs2.
        """
        game = get_game(ctx)
        msg = await ctx.send(embed=game.embed_canceled(mode))
        await add_scroll(msg)

    @commands.command(aliases=['a'])
    @check_channel('submit')
    @is_arg_in_modes()
    @commands.guild_only()
    async def archived(self, ctx, mode):
        """Display every games of a specific mode.

        Example: !embed_archived 2
        Will show every games in 2vs2, with the format below.
        id: [id], Winner: Team Red/Blue, Red team: [player1, player2],
        Blue team: [player3, player4]."""
        game = get_game(ctx)
        msg = await ctx.send(embed=game.embed_archived(mode))
        await add_scroll(msg)


def setup(bot):
    bot.add_cog(MatchProcess(bot))
