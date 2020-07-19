from datetime import datetime
import discord
from discord import Embed
from discord.ext import commands
from utils.decorators import check_category, check_channel, is_arg_in_modes
from modules.player import Player
from main import GAMES
from utils.utils import add_emojis
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game

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
        mode = int(mode)
        name = ctx.author.id
        if name in game.leaderboards[mode]:
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"There's already a played called <@{name}>."))
            return
        game.leaderboards[mode][name] = Player(ctx.author.name, ctx.author.id)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=f"<@{name}> has been registered."))
        role = discord.utils.get(
            ctx.guild.roles, name=f"{mode}vs{mode} Elo Player")
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
            role = discord.utils.get(
                ctx.guild.roles, name=f"{mode}vs{mode} Elo Player")
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
    async def join(self, ctx):
        """Let the player join a queue.

        When using it on a channel in Modes category, the user will join the
        current queue, meaning that he'll be in the list to play the next match.
        Can't be used outside Modes category.
        The user can leave afterward by using !l.
        The user needs to have previously registered in this mode."""
        game = get_game(ctx)
        mode = int(ctx.channel.name.split('vs')[0])
        name = ctx.author.id
        g_queue = game.queues[mode]
        if name in game.bans:
            game.remove_negative_bans()
            # the ban might have been removed in the function above
            if name in game.bans:
                await ctx.send(embed=Embed(color=0x000000, description=str(game.bans[name])))
                return
        if name in game.leaderboards[mode]:
            player = game.leaderboards[mode][name]
            player.id_user = ctx.author.id
            setattr(player, "last_join", datetime.now())
            res = g_queue.add_player(player, game)
            await ctx.send(embed=Embed(color=0x00FF00, description=res))
            if g_queue.is_finished():
                await ctx.send(embed=Embed(color=0x00FF00,
                    description=game.add_game_to_be_played(g_queue)))
                if g_queue.mapmode != 0:
                    msg = await ctx.send(g_queue.ping_everyone(),
                        embed=game.lobby_maps(mode, g_queue.game_id))
                    if g_queue.mapmode == 2:
                        await add_emojis(msg, game, mode, g_queue.game_id)
                if res != "Queue is full...":
                    await discord.utils.get(ctx.guild.channels,
                        name="game_announcement").\
                        send(embed=Embed(color=0x00FF00,
                        description=res),
                        content=g_queue.ping_everyone())

        else:
            await ctx.send(embed=Embed(color=0x000000,
                description="Make sure you register before joining the queue."))

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
        mode = int(ctx.channel.name.split('vs')[0])
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=game.queues[mode].remove_player(player)))

    @commands.command(aliases=['q'])
    @check_category('Solo elo')
    async def queue(self, ctx):
        """Show the current queue.

        When using it on a channel in Modes category, the user will see the
        current queue with everyone's Elo.
        Can't be used outside Modes category.
        """
        game = get_game(ctx)
        mode = int(ctx.channel.name.split('vs')[0])
        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(game.queues[mode])))

    @commands.command(aliases=['p'])
    @check_category('Solo elo')
    async def pick(self, ctx, name):
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
        mode = int(ctx.channel.name.split('vs')[0])
        g_queue = game.queues[mode]
        name, is_index = (int(name), True) if name.isdigit() else (
            name[3: -1], False)

        if not is_index:
            if not name.isdigit():
                await ctx.send("You better ping the player or use the index!")
                return
            else:
                name = int(name)
        if g_queue.mode < 2:
            await ctx.send(embed=Embed(color=0x000000,
                                       description="The mode is not a captaining mode."))
            return

        team = g_queue.get_captain_team(ctx.author.id)
        if team == 0:
            await ctx.send(embed=Embed(color=0x000000,
                                       description="You are not captain."))
            return

        team_length = (0, len(g_queue.red_team),
                       len(g_queue.blue_team))
        l_oth = team_length[1 if team == 2 else 2]
        l_my = team_length[team]

        if not ((l_oth == l_my and team == 1) or (l_oth > l_my)):
            await ctx.send(embed=Embed(color=0x000000,
                                       description="Not your turn to pick."))
            return
        if not is_index:
            player = discord.utils.get(g_queue.players, id_user=name)

            if player is None:
                await ctx.send(embed=Embed(color=0x000000,
                                           description=f"Couldn't find the player <@{name}>."))
                return
            g_queue.set_player_team(team, player)
        else:
            team = g_queue.red_team if team == 1 else g_queue.blue_team
            other_team = g_queue.red_team if team == 2 else g_queue.blue_team
            name -= 1
            if name < 0 or name >= len(g_queue.players):
                await ctx.send(embed=Embed(color=0x000000,
                                           description="Couldn't find the player with this index."))
                return
            player = g_queue.players.pop(name)
            team.append(player)

        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=f"Good pick!"))
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=str(g_queue)))
        if len(g_queue.players) == 1:
            g_queue.set_player_team(2, g_queue.players[0])
        if g_queue.is_finished():
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=str(g_queue)))
            await discord.utils.get(ctx.guild.channels,
                                    name="game_announcement").send(embed=Embed(color=0x00FF00,
                                                                               description=str(g_queue)),
                                                                   content=g_queue.ping_everyone())
            game.add_game_to_be_played(game.queues[mode])
            if g_queue.mapmode != 0:
                msg = await ctx.send(g_queue.ping_everyone(),
                    embed=game.lobby_maps(mode, g_queue.game_id))
                if g_queue.mapmode == 2:
                    await add_emojis(msg, game, mode, g_queue.game_id)

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
        mode = int(mode)
        player = await get_player_by_id(ctx, mode, ctx.author.id)
        # if ctx.author.id not in game.leaderboards[mode]:
        #     await ctx.send(embed=Embed(color=0x000000,
        #                                description=f"You must register first lol"))
        #     return
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


def setup(bot):
    bot.add_cog(Core(bot))
