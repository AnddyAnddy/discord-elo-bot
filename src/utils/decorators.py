import discord
from utils.utils import list_to_int, is_url_image
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


# def args_at_pos_digits(lst_pos_args):
#     def predicate(ctx):
#         args = ctx.message.content.split()[1:]
#         return all(args[i].isdigit() for i in lst_pos_args)
#     return commands.check(predicate)


def rank_update(GAMES, lst_pos_args):
    def args_at_pos_digits(args):
        return all(i < len(args) and args[i].isdigit() for i in lst_pos_args)

    def max_greater_min(args):
        from_points, to_points = list_to_int(args[3: 4])
        return from_points < to_points

    def url_image(args):
        return is_url_image(args[2])

    def name_in_rank(ctx, args):
        return args[1] not in GAMES[ctx.guild.id].ranks[int(args[0])]

    def predicate(ctx):
        args = ctx.message.content.split()[1:]

        return args_at_pos_digits(args) and max_greater_min(args)\
            and url_image(args) and name_in_rank(ctx, args)
    return commands.check(predicate)
