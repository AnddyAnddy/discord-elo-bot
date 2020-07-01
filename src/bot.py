"""Bot core."""


import os
import _pickle as pickle
import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from dotenv import load_dotenv
from player import Player
from game import Game
from queue_elo import Queue
from decorators import is_arg_in_modes
from decorators import check_category
from decorators import check_channel

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')


BOT = commands.Bot(command_prefix='!')
GAMES = {}

def add_attribute(game, attr_name, value):
    """Add an attribute to every player when I manually update."""
    for mode in game.leaderboards:
        for player in game.leaderboards[mode]:
            if not hasattr(player, attr_name):
                setattr(player, attr_name, value)


def load_file_to_game(guild_id):
    """Load the file from ./data/guild_id to Game if exists, return True."""
    try:
        with open(f'./data/{guild_id}.data', "rb") as file:
            return pickle.load(file)
    except IOError:
        print("The file couldn't be loaded")


@BOT.event
async def on_ready():
    """On ready event."""
    print(f'{BOT.user} has connected\n')
    for guild in BOT.guilds:
        print(guild.name)
        GAMES[guild.id] = load_file_to_game(guild.id)
        if GAMES[guild.id] is not None:
            print(f"The file from data/{guild.id}.data was correctly loaded.")
        else:
            GAMES[guild.id] = Game(guild.id)


def check_if_premium(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(
            role for role in after.roles if role not in before.roles)
        role_name = new_role.name.lower().split()
        nb_games = 0
        if "double" in role_name:
            nb_games = int(role_name[2])
        game = GAMES[after.guild.id]

        for mode in game.available_modes:
            if after.name in game.leaderboards[mode]:
                player = game.leaderboards[mode][after.name]
                player.double_xp = nb_games

        return True
    return False


@BOT.event
async def on_member_update(before, after):
    pass
    # if check_if_premium(before, after):
    #     channel = discord.utils.get(after.guild.channels, name="premium")
    #     await channel.send(f"You got your {nb_games} double xp ! \
    #     PM Anddy#2086 if you have any issue, this is available for every mode.")

    # elif before.name != after.name or before.nick != after.nick:
    #     game = GAMES[after.guild.id]
    #     old = before.nick if before.nick is not None else before.name
    #     new = after.nick if after.nick is not None else after.name
    #     for mode in game.available_modes:
    #
    #         if old in game.leaderboards[mode]:
    #             game.leaderboards[new] = game.leaderboards[mode].pop(old)
    #             game.leaderboards[new].name = new


@BOT.event
async def on_command_completion(ctx):
    """Save the data after every command."""
    if not ctx.invoked_with in ("j", "join", "ban"):
        GAMES[ctx.guild.id].save_to_file()

    # print(f"The data has been saved after the command: {ctx.message.content}")


@BOT.event
async def on_guild_channel_create(channel):
    """Save the data when a channel is created."""

    if channel.name[0].isdigit():
        GAMES[int(channel.guild.id)].save_to_file()
        print("Data has been saved since a new mode was added.")


@BOT.command(hidden=True)
@has_permissions(manage_roles=True)
async def init_elo_by_anddy(ctx):
    """Can't be used by humans.

    Initialize the bot to be ready on a guild.
    This command creates every channel needed for the Bot to work.
    This also build two categories Elo by Anddy and Modes
    Can be used anywhere. No alias, Need to have manage_roles
    """
    guild = ctx.guild
    if not discord.utils.get(guild.roles, name="Elo Admin"):
        await guild.create_role(name="Elo Admin",
                                permissions=discord.Permissions.all_channel())
        print("Elo admin created")

    if not discord.utils.get(guild.categories, name='Elo by Anddy'):
        perms_secret_chan = {
            guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
            guild.me:
                discord.PermissionOverwrite(read_messages=True),
        }

        base_cat = await guild.create_category(name="Elo by Anddy")
        await guild.create_text_channel(name="Init",
                                        category=base_cat,
                                        overwrites=perms_secret_chan)
        await guild.create_text_channel(name="Moderators",
                                        category=base_cat,
                                        overwrites=perms_secret_chan)
        await guild.create_text_channel(name="Info_chat", category=base_cat)
        await guild.create_text_channel(name="Register", category=base_cat)
        await guild.create_text_channel(name="Submit", category=base_cat)
        await guild.create_text_channel(name="Game_announcement",
                                        category=base_cat)
        await guild.create_text_channel(name="Staff_application",
                                        category=base_cat)
        await guild.create_text_channel(name="Suggestions",
                                        category=base_cat)
        await guild.create_text_channel(name="Bans",
                                        category=base_cat)
        await guild.create_text_channel(name="bye",
                                        category=base_cat)
        await guild.create_text_channel(name="premium",
                                        category=base_cat)

        await guild.create_category(name="Modes")

        print("Elo by Anddy created, init done, use !help !")


@BOT.command()
async def cmds(ctx):
    """Show every command."""
    nl = '\n'
    res = '\n - '.join([f'{command.name:<18}: {command.help.split(nl)[0]}'
        for command in sorted(BOT.commands, key=lambda c: c.name)
            if command.help is not None and not command.hidden])
    await ctx.send(embed=Embed(color=0x00FF00, description=f"```\n - {res} ```"))


@BOT.command(pass_context=True, aliases=['j'])
@check_category('Modes')
async def join(ctx):
    """Let the player join a queue.

    When using it on a channel in Modes category, the user will join the
    current queue, meaning that he'll be in the list to play the next match.
    Can't be used outside Modes category.
    The user can leave afterward by using !l.
    The user needs to have previously registered in this mode."""
    game = GAMES[ctx.guild.id]
    mode = int(ctx.channel.name[0])
    name = ctx.author.id
    if name in game.bans:
        await ctx.send(embed=Embed(color=0x000000, description=game.bans[name]))
        return
    if name in game.leaderboards[mode]:
        player = game.leaderboards[mode][name]
        res = game.queues[mode].add_player(player, game)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=res))
        if game.queues[mode].is_finished():
            await ctx.send(embed=Embed(color=0x00FF00,
                description=game.add_game_to_be_played(game.queues[mode])))
            if res != "Queue is full...":
                await discord.utils.get(ctx.guild.channels,
                    name="game_announcement").send(embed=Embed(color=0x00FF00,
                        description=res))

    else:
        await ctx.send(embed=Embed(color=0x000000,
            description="Make sure you register before joining the queue."))


@BOT.command(pass_context=True, aliases=['l'])
@check_category('Modes')
async def leave(ctx):
    """Remove the player from the queue.

    As opposite to the !join, the leave will remove the player from the
    queue if he was in.
    Can't be used outside Modes category.
    The user needs to be in the queue for using this command.
    The user can't leave a queue after it went full."""
    game = GAMES[ctx.guild.id]
    mode = int(ctx.channel.name[0])
    name = ctx.author.id

    if name in game.leaderboards[mode]:
        await ctx.send(embed=Embed(color=0x00FF00, description=game.queues[mode].
                       remove_player(game.leaderboards[mode]
                                     [name])))
    else:
        await ctx.send(embed=Embed(color=0x000000,
            description="You didn't even register lol."))


@BOT.command(aliases=['r', 'reg'])
@check_channel('register')
@check_category('Elo by Anddy')
@is_arg_in_modes(GAMES)
async def register(ctx, mode):
    """Register the player to the elo leaderboard from the mode in arg.

    Example: !r N or !r N all
    This command will register the user into the game mode set in argument.
    The game mode needs to be the N in NvsN, and it needs to already exist.
    This command can be used only in the register channel.
    The command will fail if the mode doesn't exist (use !modes to check)."""

    game = GAMES[ctx.guild.id]
    mode = int(mode)
    name = ctx.author.id
    if name in game.leaderboards[mode]:
        await ctx.send(embed=Embed(color=0x000000,
            description=f"There's already a played called <@{name}>."))
        return
    game.leaderboards[mode][name] = Player(ctx.author.name)
    await ctx.send(embed=Embed(color=0x00FF00,
        description=f"<@{name}> has been registered."))

@BOT.command(aliases=['r_all', 'reg_all'])
@check_channel('register')
@check_category('Elo by Anddy')
async def register_all(ctx):
    """Register to every available modes in one command."""
    game = GAMES[ctx.guild.id]
    name = ctx.author.id
    for mode in game.leaderboards:
        game.leaderboards[mode][name] = Player(ctx.author.name)
    await ctx.send(embed=Embed(color=0x00FF00,
        description=f"<@{name}> has been registered for every modes."))

@BOT.command(aliases=['quit'])
@check_category('Elo by Anddy')
@check_channel('bye')
async def quit_elo(ctx):
    """Delete the user from the registered players.

    The user will lose all of his data after the command.
    Can be used only in Bye channel.
    Can't be undone."""
    game = GAMES[ctx.guild.id]
    name = ctx.author.id

    game.erase_player_from_queues(name)
    game.erase_player_from_leaderboards(name)

    await ctx.send(embed=Embed(color=0x00FF00,
        description=f'<@{name}> has been removed from the rankings'))


@BOT.command()
@has_permissions(kick_members=True)
@check_category('Elo by Anddy')
@check_channel('bye')
async def force_quit(ctx, name):
    """Delete the seized user from the registered players.

    Example: !force_quit @Anddy
    The command is the same than quit_elo except that the user has to make
    someone else quit the Elo.
    This can be used only in Bye channel.
    Can't be undone."""
    game = GAMES[ctx.guild.id]
    name = int(name[3: -1])
    game.erase_player_from_queues(name)
    game.erase_player_from_leaderboards(name)

    await ctx.send(embed=Embed(color=0x00FF00,
        description=f'<@{name}> has been removed from the rankings'))


@BOT.command(aliases=['lb'])
@is_arg_in_modes(GAMES)
@check_category('Elo by Anddy')
@check_channel('info_chat')
async def leaderboard(ctx, mode, stat_key="elo"):
    """Show current leaderboard: !lb [mode] [stat key].

    Example: !lb 1 wins
    Will show the leaderboard of the mode 1vs1 based on the wins.
    [mode] can be any mode in !modes.
    [stats key] can be any stat in !info. e.g:
    name, elo, wins, losses, nb_matches, wlr
    most_wins_in_a_row, most_losses_in_a_row.
    By default, if the stats key is missing, the bot will show the elo lb.
    """
    game = GAMES[ctx.guild.id]
    await ctx.send(embed=Embed(color=0x00AAFF,
        title=f"**Elo by Anddy {mode}vs{mode} leaderboard**",
        description=game.leaderboard(int(mode), stat_key)))


@BOT.command(aliases=['q'])
@check_category('Modes')
async def queue(ctx):
    """Show the current queue.

    When using it on a channel in Modes category, the user will see the
    current queue with everyone's Elo.
    Can't be used outside Modes category.
    """
    game = GAMES[ctx.guild.id]
    mode = int(ctx.channel.name[0])
    await ctx.send(embed=Embed(color=0x00FF00, description=str(game.queues[int(mode)])))


@BOT.command(aliases=['cq', 'c_queue'])
@has_permissions(manage_roles=True)
@check_category('Modes')
async def clear_queue(ctx):
    """Clear the current queue."""
    game = GAMES[ctx.guild.id]
    mode = int(ctx.channel.name[0])
    last_id = game.queues[mode].game_id
    if not game.queues[mode].has_queue_been_full:
        game.queues[mode] = Queue(2 * mode, game.queues[mode].mode, last_id)
    await ctx.send(embed=Embed(color=0x00FF00,
        description="The queue is now empty"))



@BOT.command(aliases=['stats'])
@check_category('Elo by Anddy')
@check_channel('info_chat')
@is_arg_in_modes(GAMES)
async def info(ctx, mode, name=""):
    """Show the info of a player. !info [mode], !info [mode] [player]

    Example: !info 1 @Anddy
    With no argument, the !info will show the user's stats.
    With a player_name as argument, if the player exists, this will show
    is stats in the seized mode.
    Can be used only in info_chat channel.
    """
    game = GAMES[ctx.guild.id]
    mode = int(mode)
    name = ctx.author.id if not name else int(name[3: -1])
    if name in game.leaderboards[mode]:
        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(game.leaderboards[mode][name])))
    else:
        await ctx.send(embed=Embed(color=0x000000,
            description=f"No player called <@{name}>"))


@BOT.command(aliases=['h'])
@check_category('Elo by Anddy')
@check_channel('info_chat')
@is_arg_in_modes(GAMES)
async def history(ctx, mode, name=""):
    """Show every matches the user played in.

    Example: !h 1 Anddy
    With no argument, the !info will show the user's stats.
    With a player_name as argument, if the player exists, this will show
    is stats in the seized mode.
    Can be used only in info_chat channel.
    """
    game = GAMES[ctx.guild.id]
    mode = int(mode)
    name = ctx.author.name if not name else int(name[3: -1])

    if name in game.leaderboards[mode]:
        await ctx.send(embed=Embed(color=0x00FF00,
            description=game.get_history(mode, game.leaderboards[mode][name])))
    else:
        await ctx.send(embed=Embed(color=0x000000,
            description=f"No player called <@{name}>"))


@BOT.command(aliases=['s', 'game'])
@has_permissions(manage_roles=True)
@check_category('Elo by Anddy')
@check_channel('submit')
@is_arg_in_modes(GAMES)
async def submit(ctx, mode, id_game, winner):
    """Expect a format !s [mode] [id_game] [winner].

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


@BOT.command()
@has_permissions(manage_roles=True)
@check_category('Elo by Anddy')
@check_channel('submit')
@is_arg_in_modes(GAMES)
async def undo(ctx, mode, id_game):
    """Expect a format !undo [mode] [id_game].

    Example: !s 1 7
    in the mode 1vs1, in the 7th game.
    This will reset the ranking updates of this match.
    """
    game = GAMES[ctx.guild.id]
    await ctx.send(embed=Embed(color=0x00FF00,
        description=game.undo(int(mode), int(id_game))))


@BOT.command(aliases=['c', 'clear'])
@has_permissions(manage_roles=True)
@check_category('Elo by Anddy')
@check_channel('submit')
@is_arg_in_modes(GAMES)
async def cancel(ctx, mode, id_game):
    """Cancel the game given in arg. !c [mode] [game_id]

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


@BOT.command(aliases=['p'])
@has_permissions(manage_roles=True)
@check_category('Modes')
async def pick(ctx, *args):
    game = GAMES[ctx.guild.id]
    mode = int(ctx.channel.name[0])
    queue = game.queues[mode]
    if queue.mode < 2:
        await ctx.send(embed=Embed(color=0x000000,
            description="The mode is not a captaining mode."))
        return

    team = queue.get_captain_team(ctx.author.name)
    if team == 0:
        await ctx.send(embed=Embed(color=0x000000,
            description="You are not captain."))
        return
    player = discord.utils.get(queue.players, name=args[0])
    if player is None:
        await ctx.send(embed=Embed(color=0x000000,
            description=f"Couldn't find the player {player.name}."))
        return
    queue.set_player_team(player, team)
    await ctx.send(embed=Embed(color=0x00FF00,
        description=f"Good pick!"))


@BOT.command(aliases=['u'])
@check_category('Elo by Anddy')
@check_channel('submit')
@is_arg_in_modes(GAMES)
async def undecided(ctx, mode):
    """Display every games of a specific mode, its score or undecided. !u [mode]

    Example: !undecided 2
    Will show every undecided games in 2vs2, with the format below.
    id: [id], Red team: [player1, player2], Blue team: [player3, player4]."""
    game = GAMES[ctx.guild.id]
    await ctx.send(embed=Embed(color=0x00FF00,
        description="Undecided games: \n" + game.undecided(int(mode))))


@BOT.command(aliases=['a'])
@check_category('Elo by Anddy')
@check_channel('submit')
@is_arg_in_modes(GAMES)
async def archived(ctx, mode):
    """Display every games of a specific mode, its score or undecided. !u [mode]

    Example: !archived 2
    Will show every games in 2vs2, with the format below.
    id: [id], Winner: Team Red/Blue, Red team: [player1, player2],
    Blue team: [player3, player4]."""
    game = GAMES[ctx.guild.id]
    await ctx.send(embed=Embed(color=0x00FF00,
        description="Archived games: \n" + game.archived(int(mode))))


@BOT.command()
@has_permissions(manage_roles=True)
@check_category('Elo by Anddy')
@check_channel('init')
async def add_mode(ctx, mode):
    """Add a mode to the game modes.

    Example: !add_mode 4
    Will add the mode 4vs4 into the available modes, a channel will be
    created and the leaderboard will now have a 4 key.
    Can be used only in init channel by a manage_roles having user."""
    if mode.isdigit() and int(mode) > 0:
        nb_p = int(mode)
        if GAMES[ctx.guild.id].add_mode(nb_p):
            guild = ctx.message.guild
            category = discord.utils.get(guild.categories, name="Modes")
            await guild.create_text_channel(f'{nb_p}vs{nb_p}',
                                            category=category)
            await ctx.send(embed=Embed(color=0x00FF00,
                description="The game mode has been added."))
            return

    await ctx.send(embed=Embed(color=0x000000,
        description="Couldn't add the game mode."))


@BOT.command()
@has_permissions(manage_roles=True)
@check_category('Elo by Anddy')
@check_channel('init')
@is_arg_in_modes(GAMES)
async def delete_mode(ctx, mode):
    GAMES[ctx.guild.id].remove_mode(int(mode))
    await ctx.send(embed=Embed(color=0x00FF00,
        description="The mode has been deleted, please delete the channel."))


@BOT.command()
@check_category('Elo by Anddy')
@check_channel('info_chat')
async def modes(ctx):
    """Print available modes."""
    await ctx.send(embed=Embed(color=0x00FF00,
        description=str(GAMES[ctx.guild.id].available_modes)))


@BOT.command()
@check_category('Elo by Anddy')
@check_channel('bans')
@has_permissions(manage_roles=True)
async def ban(ctx, name, time, unity, reason=""):
    """Bans the player for a certain time in a certain unity.

    unity must be in s, m, h, d (secs, mins, hours, days).
    reason must be into " "
    """
    formats = { "s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24 }
    total_sec = int(time) * formats[unity]
    GAMES[ctx.guild.id].ban_player(int(name[3: -1]), total_sec, reason)
    await ctx.send(embed=Embed(color=0x00FF00,
        description="The player has been banned ! Check !bans"))


@BOT.command()
@check_category('Elo by Anddy')
@check_channel('bans')
@has_permissions(manage_roles=True)
async def unban(ctx, name):
    """Bans the player for a certain time in a certain unity.

    unity must be in s, m, h, d (secs, mins, hours, days).
    reason must be into " "
    """
    GAMES[ctx.guild.id].unban_player(int(name[3: -1]))
    await ctx.send(embed=Embed(color=0x00FF00,
        description="The player has been unbanned ! Check !bans"))



@BOT.command(aliases=['bans'])
@check_category('Elo by Anddy')
@check_channel('bans')
async def all_bans(ctx):
    await ctx.send(embed=Embed(color=0x00FF00,
        description=GAMES[ctx.guild.id].all_bans()))


@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(embed=Embed(color=0x000000,
            description="The command doesn't exist, check !help !"))
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send(embed=Embed(color=0x000000,
            description="You used this command with either a wrong channel or \
a wrong argument. Or maybe you don't have the permission..."))
    elif isinstance(error, MissingPermissions):
        await ctx.send(embed=Embed(color=0x000000,
            description="You must have manage_roles permission to run that."))

    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=Embed(color=0x000000,
            description=str(error)))
    else:
        raise error
BOT.run(TOKEN)
