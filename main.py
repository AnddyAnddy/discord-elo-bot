import _pickle
import asyncio
import os
import sys
from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

import src
from src.GAMES import GAMES
from src.modules import game, player, queue_elo, rank, elo, ban
from src.modules.game import Game
from src.utils.exceptions import PassException, send_error
from src.utils.utils import build_other_page

sys.modules['modules'] = src.modules
sys.modules['modules.game'] = game
sys.modules['modules.player'] = player
sys.modules['modules.queue_elo'] = queue_elo
sys.modules['modules.rank'] = rank
sys.modules['modules.elo'] = elo
sys.modules['modules.ban'] = ban


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# test guild 
# DISCORD_MAIN_GUILD_ID = 769915335968423997
# real guild
DISCORD_MAIN_GUILD_ID = 732326859039178882
intents = discord.Intents.default()
intents.members = True
BOT: Bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)
BOT.load_extension('src.commands.admin')
BOT.load_extension('src.commands.core')
BOT.load_extension('src.commands.helper')
BOT.load_extension('src.commands.infostats')
BOT.load_extension('src.commands.init')
BOT.load_extension('src.commands.matchprocess')
BOT.load_extension('src.commands.graphs')
BOT.load_extension('src.commands.premium')


def load_file_to_game(guild_id):
    """Load the file from ./data/guild_id to Game if exists."""
    try:
        with open(f"./data/{guild_id}.data", "rb") as file:
            return _pickle.load(file)
    except IOError:
        pass
        # print("The file couldn't be loaded")


@BOT.command(hidden=True)
async def ubotdate(ctx):
    res = '\n'.join([f"{guild.name:20} by + {str(guild.owner):20} {len(guild.members)} users"
                     for guild in BOT.guilds if "discord" not in guild.name.lower()])
    total_user = sum([len(guild.members) for guild in BOT.guilds])
    await BOT.change_presence(activity=discord.Game(name=f"{len(BOT.guilds)} guilds with {total_user} users"))
    await ctx.send(
        embed=Embed(color=0x00FF00,
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
            GAMES[guild.id].check_for_premium()
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
async def on_command_completion(ctx):
    """Save the data after every command."""
    GAMES[ctx.guild.id].save_to_file()

@BOT.event
async def on_command_error(ctx, error):
    inv = ctx.invoked_with
    embed = ""
    if isinstance(error, commands.errors.CommandNotFound):
        embed = Embed(color=0x000000,
                      description="The command doesn't exist, check !cmds !")

    elif isinstance(error, commands.errors.BadArgument):
        await send_error(ctx, error)
        await ctx.message.delete(delay=3)
        return

    elif isinstance(error, commands.errors.CheckFailure):
        embed = Embed(color=0x000000,
                      description="You used this command with either a wrong channel "
                                  + "or a wrong argument. Or you don't have the permission...\n")
        # await ctx.send_help(inv)

    elif isinstance(error, commands.errors.MissingPermissions):
        embed = Embed(color=0x000000,
                      description="You must have manage_roles permission to run that.")

    elif isinstance(error, commands.errors.MissingRequiredArgument):
        embed = Embed(color=0x000000,
                      description=f"{str(error)}\nCheck !help {inv}")
    elif isinstance(error, commands.DisabledCommand):
        embed = Embed(color=0x000000,
                      description="The command is disabled.")
    elif isinstance(error, discord.errors.Forbidden):
        embed = Embed(color=0x000000,
                      description="I don't have permissions to do that.")
        pass
    elif hasattr(error, "original") and isinstance(error.original, PassException):
        pass
    else:
        print(ctx)
        print(ctx.invoked_with, ctx.guild, datetime.now().strftime("%d %h %I h %M"))
        try:
            await discord.utils.get(ctx.guild.channels, name="bugs") \
                .send(f"{ctx.invoked_with}: \n{error}")
            raise error
        except AttributeError:
            await ctx.send(f"{ctx.invoked_with}: \n{error}\n")
            raise error

    try:
        await ctx.author.send(embed=embed)
        await ctx.message.delete(delay=3)

    except Exception:
        await ctx.send(f"Please {ctx.author.mention}, allow my dms.")


BOT.run(TOKEN)
