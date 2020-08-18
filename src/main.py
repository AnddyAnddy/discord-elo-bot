import sys
import _pickle
import os
import discord
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed
from GAMES import GAMES
from utils.utils import check_if_premium, build_other_page, rename_attr
from modules.queue_elo import Queue
from modules.game import Game
from utils.exceptions import PassException, send_error

from modules import game, player, queue_elo, rank, elo, ban

sys.modules['game'] = game
sys.modules['player'] = player
sys.modules['queue_elo'] = queue_elo
sys.modules['rank'] = rank
sys.modules['elo'] = elo
sys.modules['ban'] = ban

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_MAIN_GUILD_ID = 732326859039178882
BOT = commands.Bot(command_prefix='!', case_insensitive=True)
BOT.load_extension('commands.admin')
BOT.load_extension('commands.core')
BOT.load_extension('commands.helper')
BOT.load_extension('commands.info_stats')
BOT.load_extension('commands.init')
BOT.load_extension('commands.match_process')
BOT.load_extension('commands.graphs')
BOT.load_extension('commands.premium')


def load_file_to_game(guild_id):
    """Load the file from ./data/guild_id to Game if exists, return True."""
    try:
        with open(f"./data/{guild_id}.data", "rb") as file:
            return _pickle.load(file)
    except IOError:
        pass
        # print("The file couldn't be loaded")


def mode_to_mode_s(game):
    for k, v in game.__dict__.items():
        if isinstance(v, dict):
            if any(e in v for e in range(1, 10)):
                setattr(game, k, {f'{mode}s': val for mode,
                        val in v.items() if str(mode).isdigit()})
    game.available_modes = set(game.leaderboards.keys())

@BOT.command(hidden=True)
async def ubotdate(ctx):
    res = '\n'.join([f'{guild.name:20} by + {str(guild.owner):20} {len(guild.members)} users'
        for guild in BOT.guilds if "discord" not in guild.name.lower()])
    total_user = sum([len(guild.members) for guild in BOT.guilds])
    await BOT.change_presence(activity=discord.Game(name=f"{len(BOT.guilds)} guilds with {total_user} users"))
    await ctx.send(embed=Embed(color=0x00FF00,
        title="Guilds infos",
        description=res)
    )


@BOT.event
async def on_ready():
    """On ready event."""
    print(f'{BOT.user} has connected\n')
    total_user = 0
    for guild in BOT.guilds:
        print(f'{guild.name:20} by + {str(guild.owner):20} {len(guild.members)} users')
        if guild.name != "Discord Bot List":
            total_user += len(guild.members)

        GAMES[guild.id] = load_file_to_game(guild.id)
        if GAMES[guild.id] is not None:
            GAMES[guild.id].clear_undecided_reacted()
            # print(f"The file from data/{guild.id}.data was correctly loaded.")
        else:
            GAMES[guild.id] = Game(guild.id)

    print(f'\n\n{total_user} users in total, with {len(BOT.guilds)} guilds')
    await BOT.change_presence(activity=discord.Game(name=f"{len(BOT.guilds)} guilds with {total_user} users"))

@BOT.event
async def on_guild_join(guild):
    """Send instruction message on join."""
    print(f"I just joined the guild {guild} {guild.id}")
    channel = next(channel for channel in guild.channels
        if channel.type == discord.ChannelType.text)
    await channel.send(embed=Embed(color=0x00A000,
        title="Hey, let's play together !",
        description="Oh hey i'm new around here !\n"
            "To set me up, someone will have to "
            "write `!init_elo_by_anddy` somewhere and the black magic "
            "will handle the rest.\n"
            "Any issue ? https://discord.gg/E2ZBNSx"))


@BOT.event
async def on_reaction_add(reaction, user):
    """

    @param user: discord.User
    @type reaction: discord.Reaction
    """
    res = build_other_page(BOT, GAMES[user.guild.id], reaction, user)
    if res is None:
        return
    await reaction.message.edit(embed=res)

    await reaction.message.remove_reaction(reaction.emoji, user)


@BOT.event
async def on_member_update(before, after):
    if before.bot:
        return
    discord_id = DISCORD_MAIN_GUILD_ID
    if discord_id not in GAMES:
        return
    if before.guild.id == discord_id and check_if_premium(GAMES[discord_id], before, after):
        channel = discord.utils.get(after.guild.channels, name="premium")
        await channel.send(f"Hi <@{before.id}>, You got your {nb_games} double xp ! "
            "this is available for every mode you're registered."
            "You simply have to use !premium in #register in your server."
            "Any issue ? PM Anddy#2086.")


@BOT.event
async def on_command_completion(ctx):
    """Save the data after every command."""
    GAMES[ctx.guild.id].save_to_file()


@BOT.event
async def on_command_error(ctx, error):
    inv = ctx.invoked_with
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(embed=Embed(color=0x000000,
           description="The command doesn't exist, check !cmds !"))

    elif isinstance(error, commands.errors.BadArgument):
        await send_error(ctx, error)

    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send(embed=Embed(color=0x000000,
           description="You used this command with either a wrong channel "
           + "or a wrong argument. Or you don't have the permission...\n"))
        # await ctx.send_help(inv)

    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send(embed=Embed(color=0x000000,
           description="You must have manage_roles permission to run that."))

    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=Embed(color=0x000000,
           description=f"{str(error)}\nCheck !help {inv}"))
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send(embed=Embed(color=0x000000,
            description="The command is disabled."))
    elif isinstance(error, discord.errors.Forbidden):
        pass
    elif hasattr(error, "original") and isinstance(error.original, PassException):
        pass
    else:
        print(ctx.invoked_with, ctx.guild, datetime.now().strftime("%d %h %I h %M"))
        try:
            await discord.utils.get(ctx.guild.channels, name="bugs")\
                .send(f"{ctx.invoked_with}: \n{error}")
        except AttributeError:
            await ctx.send(f"{ctx.invoked_with}: \n{error}\n")
        raise error

BOT.run(TOKEN)
