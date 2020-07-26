import discord
from utils.utils import list_to_int, is_url_image
from discord.ext import commands
from utils.exceptions import get_game
from utils.exceptions import get_channel_mode


def is_arg_in_modes(games):
    def predicate(ctx):
        args = ctx.message.content.split(' ')
        if len(args) < 2:
            raise commands.errors.BadArgument(
                "The mode argument is missing.")
        if args[1] not in get_game(ctx).available_modes:
            raise commands.errors.BadArgument(
                f"The mode is incorrect, you wrote {args[1]}\n"
                f"But it must be in {str(get_game(ctx).available_modes)}"
            )

        return True

    return commands.check(predicate)


def check_category(*names):
    def predicate(ctx):
        guild = ctx.guild
        ctx_cat = ctx.channel.category
        for name in names:
            to_be_cat = discord.utils.get(guild.categories, name=name)
            if to_be_cat is None:
                raise ValueError(f"Parameter {name} isn't a real category")
            if ctx_cat == to_be_cat:
                return True
        raise commands.errors.BadArgument(
            f"You should write this message in {name} category"
        )

    return commands.check(predicate)


def check_channel(name):
    def predicate(ctx):
        guild = ctx.guild
        ctx_channel = ctx.channel
        to_be_channel = discord.utils.get(guild.channels, name=name)
        if to_be_channel is None:
            raise ValueError(f"Parameter {name} isn't a real channel")
        if ctx_channel != to_be_channel:
            raise commands.errors.BadArgument(
                f"You should write this command in #{name}.")
        return True

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


def has_role_or_above(roleName):
    def predicate(ctx):
        role = discord.utils.get(ctx.guild.roles, name=roleName)
        if role is None or ctx.author.top_role >= role:
            return True
        raise commands.errors.BadArgument(
            f"You don't have the permission to run this command.\n"
            f"You must be at least {roleName}."
        )
    return commands.check(predicate)


def check_if_banned(games):
    def predicate(ctx):
        game = games[ctx.guild.id]
        id = ctx.author.id
        if id in game.bans:
            game.remove_negative_bans()
            # the ban might have been removed in the function above
            if id in game.bans:
                raise commands.errors.BadArgument(str(game.bans[id]))
        return True
    return commands.check(predicate)


def check_captain_mode(games):
    def predicate(ctx):
        game = games[ctx.guild.id]
        mode = get_channel_mode(ctx)
        queue = game.queues[mode]
        if queue.mode < 2:
            raise commands.errors.BadArgument("This mode doesn't allow picks")
        if not queue.has_queue_been_full:
            raise commands.errors.BadArgument(
                "The pick session hasn't started")
        return True
    return commands.check(predicate)
