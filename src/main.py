import sys
import _pickle
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed
from GAMES import GAMES
from utils.utils import check_if_premium, build_other_page

from modules import game, player, queue_elo, rank, elo, ban

sys.modules['game'] = game
sys.modules['player'] = player
sys.modules['queue_elo'] = queue_elo
sys.modules['rank'] = rank
sys.modules['elo'] = elo
sys.modules['ban'] = ban

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
BOT = commands.Bot(command_prefix='!')
BOT.load_extension('commands.admin')
BOT.load_extension('commands.core')
BOT.load_extension('commands.helper')
BOT.load_extension('commands.info_stats')
BOT.load_extension('commands.init')
BOT.load_extension('commands.match_process')



def load_file_to_game(guild_id):
    """Load the file from ./data/guild_id to Game if exists, return True."""
    try:
        with open(f"./data/{guild_id}.data", "rb") as file:
            return _pickle.load(file)
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
    nb_games = check_if_premium(GAMES[after.guild.id], before, after)
    if nb_games:
        channel = discord.utils.get(after.guild.channels, name="premium")
        await channel.send(f"Hi {before.name}, You got your {nb_games} double xp ! \
        PM Anddy#2086 if you have any issue, this is available for every mode.")

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

    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send(embed=Embed(color=0x000000,
           description="You used this command with either a wrong channel or \
           a wrong argument.\
           Or maybe you don't have the permission...\n"\
           f"Check !help {inv}"))

    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send(embed=Embed(color=0x000000,
           description="You must have manage_roles permission to run that."))

    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=Embed(color=0x000000,
           description=f"{str(error)}\nCheck !help {inv}"))
    else:
        print(ctx.invoked_with)
        await discord.utils.get(ctx.guild.channels, name="bugs")\
            .send(f"{ctx.invoked_with}: \n{error}")
        raise error

BOT.run(TOKEN)
