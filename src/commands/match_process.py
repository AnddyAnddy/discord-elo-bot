from discord import Embed
from main import GAMES
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from utils.decorators import check_category, check_channel, is_arg_in_modes, has_role_or_above
from utils.utils import team_name, get_elem_from_embed
from utils.utils import autosubmit_reactions, map_pick_reactions
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game
from utils.utils import add_scroll



class Match_process(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
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
            await autosubmit_reactions(reaction, user, game)
            return
        if reaction.emoji in game.available_maps.values():
            await map_pick_reactions(reaction, user, game)
            return

        await reaction.message.remove_reaction(reaction.emoji, user)


    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.id == self.bot.user.id or not reaction.message.embeds:
            return
        game = GAMES[user.guild.id]
        # red, blue, draw, cancel
        await autosubmit_reactions(reaction, user, game, True)


    @commands.command(aliases=['as'])
    @check_channel('autosubmit')
    @is_arg_in_modes(GAMES)
    async def autosubmit(self, ctx, mode, id_game, winner):
        """Submit the score of a game.

        Example: !s 1 7 1
        in the mode 1vs1, in the 7th game, the team 1 (red) won.
        This will update NOT the rankings until the game is approved.
        """
        game = get_game(ctx)
        if not id_game.isdigit() or not winner.isdigit():
            raise commands.errors.MissingRequiredArgument(id_game)
        id_game, winner = int(id_game), int(winner)
        if not id_game in game.undecided_games[mode]:
            await ctx.send(embed=Embed(color=0x000000,
                description="The game is not in undecided games!"))
            return
        if winner not in range(3):
            await ctx.send(embed=Embed(color=0x000000,
                description="The winner must be in [0, 1, 2]!"))
            return

        queue = game.undecided_games[mode][id_game]
        if not mode in game.waiting_for_approval:
            game.waiting_for_approval[mode] = {}
        game.waiting_for_approval[mode][id_game] = queue
        nb_yes = int(queue.max_queue // 2 + 1)
        nb_no = int(queue.max_queue // 2)
        res = f"<@{ctx.author.id}> is saying that {team_name(winner)} won.\n"
        res += f"Do you confirm ? {nb_yes + 1} ✅ are needed to make it official.\n"
        res += f'{nb_no + 1} ❌ {"is" if nb_no + 1 == 1 else "are"} needed to cancel it.\n'
        res += "Any attempt to mess up the result will lead to a ban."

        msg = await ctx.send(queue.ping_everyone(),
            embed=Embed(title="autosubmit",
            color=0xFF0000 if winner == 1 else 0x0000FF,
            description=res)\
                .add_field(name="name", value="autosubmit") \
                .add_field(name="winner", value=winner) \
                .add_field(name="mode", value=mode) \
                .add_field(name="id", value=id_game) \
                .set_footer(text=f"[ 1 / 1 ]"))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")








    @commands.command(aliases=['s', 'game'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
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
    @is_arg_in_modes(GAMES)
    async def undo(self, ctx, mode, id_game):
        """Undo a game.

        Example: !undo 1 7
        in the mode 1vs1, in the 7th game.
        This will reset the ranking updates of this match.
        The game will be in undecided.
        """
        game = get_game(ctx)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=game.undo(mode, int(id_game))))

    @commands.command(aliases=['c', 'clear'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def cancel(self, ctx, mode, id_game):
        """Cancel the game given in arg.

        Example: !cancel 1 3
        will cancel the game with the id 3 in the mode 1vs1.
        """
        game = get_game(ctx)
        if game.cancel(mode, int(id_game)):
            await ctx.send(embed=Embed(color=0x00FF00,
                description=f"The game {id_game} has been canceled"))
        else:
            await ctx.send(embed=Embed(color=0x000000,
                description=f"Couldn't find the game {id_game} in the current games."))

    @commands.command(aliases=['uc', 'uclear'])
    @has_role_or_above('Elo Admin')
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
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
    @is_arg_in_modes(GAMES)
    async def undecided(self, ctx, mode):
        """Display every undecided games.

        Example: !undecided 2
        Will show every undecided games in 2vs2, with the format below.
        id: [id], Red team: [player1, player2], Blue team: [player3, player4]."""
        game = get_game(ctx)
        msg = await ctx.send(embed=game.undecided(mode))
        await add_scroll(msg)

    @commands.command(aliases=['cl'])
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def canceled(self, ctx, mode):
        """Display every canceled games of a specific mode.

        Example: !cl 2
        Will show every canceled games in 2vs2.
        """
        game = get_game(ctx)
        msg = await ctx.send(embed=game.canceled(mode))
        await add_scroll(msg)

    @commands.command(aliases=['a'])
    @check_channel('submit')
    @is_arg_in_modes(GAMES)
    async def archived(self, ctx, mode):
        """Display every games of a specific mode.

        Example: !archived 2
        Will show every games in 2vs2, with the format below.
        id: [id], Winner: Team Red/Blue, Red team: [player1, player2],
        Blue team: [player3, player4]."""
        game = get_game(ctx)
        msg = await ctx.send(embed=game.archived(mode))
        await add_scroll(msg)


def setup(bot):
    bot.add_cog(Match_process(bot))
