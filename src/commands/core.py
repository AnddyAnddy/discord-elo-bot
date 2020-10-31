import discord
import random
from discord import Embed
from discord.ext import commands

from main import GAMES
from src.modules.player import Player
from src.utils.decorators import check_category, check_channel, is_arg_in_modes, check_if_banned, check_captain_mode
from src.utils.exceptions import PassException
from src.utils.exceptions import get_captain_team
from src.utils.exceptions import get_channel_mode
from src.utils.exceptions import get_game
from src.utils.exceptions import get_player_by_id, get_player_by_mention
from src.utils.exceptions import send_error
from src.utils.utils import finish_the_pick, pick_players, join_aux
from src.utils.utils import join_team_reaction
from src.utils.utils import split_with_numbers


class Core(commands.Cog):
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
        if reaction.emoji in "👍👎":
            await join_team_reaction(reaction, user, game)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_reaction_remove(self, reaction, user):
        if user.id == self.bot.user.id or not reaction.message.embeds:
            return
        game = GAMES[user.guild.id]
        if reaction.emoji in "👍👎":
            await join_team_reaction(reaction, user, game)

    @commands.command(aliases=['r', 'reg'])
    @check_channel('register')
    @is_arg_in_modes()
    @commands.guild_only()
    async def register(self, ctx, mode):
        """Register the player to the elo embed_leaderboard.

        Example: !r N or !r N all
        This command will register the user into the game mode set in argument.
        The game mode needs to be the N in NvsN, and it needs to already exist.
        This command can be used only in the register channel.
        The command will fail if the mode doesn't exist (use !modes to check)."""

        game = get_game(ctx)
        name = ctx.author.id
        if name in game.leaderboard(mode):
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"There's already a played called <@{name}>."))
            return
        if len(game.leaderboard(mode)) < game.limit_leaderboards:
            game.leaderboard(mode)[name] = Player(ctx.author.name, ctx.author.id)
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"<@{name}> has been registered."))
            num = split_with_numbers(mode)[0]
            role = discord.utils.get(
                ctx.guild.roles, name=f"{num}vs{num} Elo Player")
            await ctx.author.add_roles(role)
        else:
            await ctx.send(embed=Embed(color=0x000000,
                                       description="This server doesn't have premium, hence, it is limited to 10 "
                                                   "users only.\n Get premium here: https://discord.gg/E2ZBNSx to "
                                                   "get unlimited users !"))

    @commands.command(aliases=['r_all', 'reg_all'])
    @check_channel('register')
    @commands.guild_only()
    async def register_all(self, ctx):
        """Register to every available modes in one command."""
        game = get_game(ctx)
        name = ctx.author.id
        for mode in game.get_leaderboards():
            if name not in game.leaderboard(mode):
                game.leaderboard(mode)[name] = Player(
                    ctx.author.name, ctx.author.id)
            num = int(split_with_numbers(mode)[0])

            role = discord.utils.get(ctx.guild.roles, name=f"{num}vs{num} Elo Player")
            # role may have been deleted...
            if role is not None:
                await ctx.author.add_roles(role)
            else:
                await ctx.message.guild.create_role(name=f"{num}vs{num} Elo Player",
                                                    colour=discord.Colour(random.randint(0, 0xFFFFFF)))
                await ctx.author.add_roles(role)

        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=f"<@{name}> has been registered for every mode."))

    @commands.command(aliases=['quit'], enabled=False)
    @check_channel('register')
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
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
        """
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        queue = game.queues[mode]
        team_id = await get_captain_team(ctx, queue, mode, ctx.author.id)
        await pick_players(ctx, queue, mode, team_id, p1, p2)
        await finish_the_pick(ctx, game, queue, mode, team_id)

    @commands.command(aliases=['pos'])
    @check_channel('register')
    @is_arg_in_modes()
    @commands.guild_only()
    async def fav_positions(self, ctx, mode, *args):
        """Put the order of your positions from your preferred to the least preferred.

        Example:
        !pos 4 dm st gk am
        Will tell the bot that my preferred position is dm, then st, then gk...
        And it will be shown on the queue.
        """
        game = get_game(ctx)
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        if len(args) > len(game.available_positions) or \
                any(elem for elem in args if elem not in game.available_positions):
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"Your positions could not be saved, "
                                                   f"all of your args must be in {game.available_positions}"))
            return

        setattr(player, "fav_pos", list(args))
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="Your positions have been saved!"))

    @commands.command()
    @check_channel('register')
    @commands.guild_only()
    async def rename(self, ctx, new_name=""):
        """Will rename the user in every leaderboards.

        With no argument, the user will have his name reset.
        Only usable in #register
        """
        game = get_game(ctx)
        if not new_name:
            new_name = ctx.author.nick if ctx.author.nick is not None else ctx.author.name
        for mode in game.get_leaderboards():
            if ctx.author.id in game.leaderboard(mode):
                game.leaderboard(mode)[ctx.author.id].name = new_name
        await ctx.send(f"You have been renamed to {new_name}")

    @commands.command(aliases=['jw'])
    @check_category("Teams elo")
    @commands.guild_only()
    async def join_with(self, ctx, *mentions):
        """Join the queue with your own team.

        Example in 4vs4:
        !jw @player1 @player2 @player3
        """
        mode = get_channel_mode(ctx)
        nb_players = int(split_with_numbers(mode)[0])
        players = {await get_player_by_id(ctx, mode, ctx.author.id)} | \
                  {await get_player_by_mention(ctx, mode, m) for m in mentions}
        if nb_players != len(players):
            await send_error(ctx, f"You joined with {len(players)} player(s) but you need exactly {nb_players}")
            raise PassException()

        embed = Embed(title=f"Invitations for {mode} from {ctx.author.display_name}",
                      description="To join with your team, everyone involved have to confirm by clicking on 👍.\n"
                                  "To deny, click on the 👎.") \
            .add_field(name=f"Captain", value=ctx.author.mention)

        for i in range(len(mentions)):
            embed.add_field(name=f"Player n°{i + 1}", value=mentions[i])

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(aliases=['lw'])
    @check_category("Teams elo")
    @commands.guild_only()
    async def leave_with(self, ctx):
        game = get_game(ctx)
        mode = get_channel_mode(ctx)
        queue = game.queues[mode]
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        if player in queue.players:
            # The queue is full after the second team gets added so they can't leave anyway
            queue.players = queue.players[queue.max_queue // 2:]
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description="Your team was removed from the queue."))
            return
        await send_error(ctx, "You are not in the queue.")


def setup(bot):
    bot.add_cog(Core(bot))
