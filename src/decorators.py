import discord
from discord.ext import commands


def is_arg_in_modes(games):
    def predicate(ctx):
        args = ctx.message.content.split(' ')
        modes = games[ctx.guild.id].available_modes
        return len(args) >= 2 and \
               args[1].isdigit() and \
               int(args[1]) in modes

    return commands.check(predicate)


def check_category(name):
    def predicate(ctx):
        guild = ctx.guild
        ctx_cat = ctx.channel.category
        to_be_cat = discord.utils.get(guild.categories, name=name)
        if to_be_cat is None:
            raise ValueError(f"Parameter {name} isn't a real category")
        return ctx_cat == to_be_cat

    return commands.check(predicate)


def check_channel(name):
    def predicate(ctx):
        guild = ctx.guild
        ctx_channel = ctx.channel
        to_be_channel = discord.utils.get(guild.channels, name=name)
        if to_be_channel is None:
            raise ValueError(f"Parameter {name} isn't a real channel")
        return ctx_channel == to_be_channel

    return commands.check(predicate)
