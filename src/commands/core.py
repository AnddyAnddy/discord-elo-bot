from datetime import datetime
import discord
from discord import Embed
from discord.ext import commands
from utils.decorators import check_category, check_channel, is_arg_in_modes, check_if_banned, check_captain_mode
from modules.player import Player
from main import GAMES
from utils.utils import add_emojis, set_map, announce_game, finish_the_pick, team_name, pick_players, join_aux
from utils.utils import split_with_numbers
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game
from utils.exceptions import get_picked_player
from utils.exceptions import get_captain_team
from utils.exceptions import get_channel_mode
from utils.exceptions import send_error
from utils.exceptions import PassException

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['r', 'reg'])
    @check_channel('register')
    @is_arg_in_modes(GAMES)
    async def register(self, ctx, mode):
        """Register the player to the elo leaderboard.

        Example: !r N or !r N all
        This command will register the user into the game mode set in argument.
        The game mode needs to be the N in NvsN, and it needs to already exist.
        This command can be used only in the register channel.
        The command will fail if the mode doesn't exist (use !modes to check)."""

        game = get_game(ctx)
        name = ctx.author.id
        if name in game.leaderboards[mode]:
            await ctx.send(embed=Embed(color=0x000000,
                description=f"There's already a played called <@{name}>."))
            return
        game.leaderboards[mode][name] = Player(ctx.author.name, ctx.author.id)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=f"<@{name}> has been registered."))
        num = split_with_numbers(mode)[0]
        role = discord.utils.get(
            ctx.guild.roles, name=f"{num}vs{num} Elo Player")
        await ctx.author.add_roles(role)

    @commands.command(aliases=['r_all', 'reg_all'])
    @check_channel('register')
    async def register_all(self, ctx):
        """Register to every available modes in one command."""
        game = get_game(ctx)
        name = ctx.author.id
        for mode in game.leaderboards:
            if name not in game.leaderboards[mode]:
                game.leaderboards[mode][name] = Player(
                    ctx.author.name, ctx.author.id)
            num = int(split_with_numbers(mode)[0])
            role = discord.utils.get(
                ctx.guild.roles, name=f"{num}vs{num} Elo Player")
            await ctx.author.add_roles(role)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=f"<@{name}> has been registered for every mode."))

    @commands.command(aliases=['quit'])
    @check_channel('register')
    async def quit_elo(self, ctx):
        """Delete the user from the registered players.

        The user will lose all of his data after the command.
        Can be used only in Bye channel.
        Can't be undone."""
        game = get_game(ctx)
        id = ctx.author.id

        game.erase_player_from_queues(id)
        game.erase_player_from_leaderboards(id)

        await ctx.send(embed=Embed(color=0x00FF00,
            description=f'<@{id}> has been removed from the rankings'))

    @commands.command(pass_context=True, aliases=['j'])
    @check_category('Solo elo')
    @check_if_banned(GAMES)
    async def join(self, ctx):
        """Let the player join a queue.

        When using it on a channel in Modes category, the user will join the
        current queue, meaning that he'll be in the list to play the next match.
        Can't be used outside Modes category.
        The user can leave afterward by using !l.
        The user needs to have previously registered in this mode."""
        await join_aux(ctx)

    @commands.command(pass_context=True, aliases=['l'])
    @check_category('Solo elo')
    async def leave(self, ctx):
        """Remove the player from the queue.

        As opposite to the !join, the leave will remove the player from the
        queue if he was in.
        Can't be used outside Modes category.
        The user needs to be in the queue for using this command.
        The user can't leave a queue after it went full."""
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=game.queues[mode].remove_player(player)))

    @commands.command(aliases=['q'])
    @check_category('Solo elo', 'Teams elo')
    async def queue(self, ctx):
        """Show the current queue.

        When using it on a channel in Modes category, the user will see the
        current queue with everyone's Elo.
        Can't be used outside Modes category.
        """
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(game.queues[mode])))

    @commands.command(aliases=['p'])
    @check_category('Solo elo')
    @check_captain_mode(GAMES)
    async def pick(self, ctx, p1, p2=""):
        """Pick a player in the remaining player.

        Let's say Anddy is the red captain, and it's his turn to pick.
        Remaining players:
        1) @orp
        2) @grünersamt
        To pick orp, Anddy can either do:
        !p @orp
        or
        !p 1
        You can only pick players one by one, the index may change after a pick.
        """
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        queue = game.queues[mode]
        team_id = await get_captain_team(ctx, queue, mode, ctx.author.id)
        await pick_players(ctx, queue, mode, team_id, p1, p2)
        await finish_the_pick(ctx, game, queue, mode, team_id)


    @commands.command(aliases=['pos'])
    @check_channel('register')
    @is_arg_in_modes(GAMES)
    async def fav_positions(self, ctx, mode, *args):
        """Put the order of your positions from your prefered to the least prefered.

        Example:
        !pos 4 dm st gk am
        Will tell the bot that my prefered position is dm, then st, then gk...
        And it will be shown on the queue.
        """
        game = get_game(ctx)
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        if len(args) > len(game.available_positions) or \
                any(elem for elem in args if elem not in game.available_positions):
            await ctx.send(embed=Embed(color=0x000000,
                description=f"Your positions couldn't be saved, "\
                    f"all of your args must be in {game.available_positions}"))
            return

        setattr(player, "fav_pos", list(args))
        await ctx.send(embed=Embed(color=0x00FF00,
            description="Your positions have been saved!"))

    @commands.command()
    @check_channel('register')
    async def rename(self, ctx, new_name=""):
        """Will rename the user in every leaderboards.

        With no argument, the user will have his name resetted.
        Only usable in #register
        """
        game = get_game(ctx)
        if not new_name:
            new_name = ctx.author.nick if ctx.author.nick is not None else ctx.author.name
        for mode in game.leaderboards:
            if ctx.author.id in game.leaderboards[mode]:
                game.leaderboards[mode][ctx.author.id].name = new_name
        await ctx.send(f"You have been renamed to {new_name}")

    @commands.command(aliases=['jw'])
    @check_category("Teams elo")
    async def join_with(self, ctx, *mentions):
        """Join the queue with your own team.

        Example in 4vs4:
        !jw @player1 @player2 @player3
        """
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        queue = game.queues[mode]
        nb_players = int(split_with_numbers(mode)[0])
        players = {await get_player_by_id(ctx, mode, ctx.author.id)} |\
            {await get_player_by_mention(ctx, mode, m) for m in mentions}
        if nb_players != len(players):
            await send_error(ctx, f"You joined with {len(players)} player(s) but you need exactly {nb_players}")
            raise PassException()

        res = await queue.add_players(ctx, players, game)
        if res:
            await ctx.send(embed=Embed(color=0x00FF00, description=res))
            if queue.is_finished():
                await ctx.send(embed=Embed(color=0x00FF00,
                    description=game.add_game_to_be_played(queue, mode)))
                await set_map(ctx, game, queue, mode)
                await announce_game(ctx, res, queue)
def setup(bot):
    bot.add_cog(Core(bot))
