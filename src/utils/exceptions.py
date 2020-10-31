from discord import Embed

from src.GAMES import GAMES


class IncorrectName(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Incorrect argument:\n" + \
               f"{self.name} is not in my data.\n" + \
               "Maybe he did not register.\n" \
               "Used as an argument, you need to mention the user (ex: @Anddy)."


class PassException(Exception):
    pass


async def send_error(ctx, desc):
    try:

        await ctx.author.send(embed=Embed(title="Error !", color=0x000000,
                                          description=f"{str(desc)}\nRead !help {ctx.invoked_with}"))
    except Exception:
        pass
    # await ctx.author.send_help(ctx.invoked_with)


def get_game(ctx):
    """Return the game corresponding to the context's guild."""
    return GAMES[ctx.guild.id]


async def get_player_by_id(ctx, mode, id):
    game = get_game(ctx)
    if str(id).isdigit() and int(id) in game.leaderboard(mode):
        return game.leaderboard(mode)[int(id)]

    await send_error(ctx, IncorrectName(f"<@{id}>"))
    raise PassException()


async def get_player_by_mention(ctx, mode, mention):
    """Return the player from the embed_leaderboard if exists or raise IncorrectName."""
    # Mention is a string in the <@long_number_id> format
    id = mention[3: -1]
    return await get_player_by_id(ctx, mode, id)


async def get_id(ctx, mention):
    id = mention[3: -1]
    if id.isdigit() and int(id):
        return int(id)

    await send_error(ctx, IncorrectName(mention))
    raise PassException()


async def get_player_on_queue(ctx, queue, pos):
    try:
        if pos < 1:  # create an error since the index has to be > 1
            return queue.players[len(queue.players) + 1]
        return queue.players[pos - 1]
    except IndexError:
        await send_error(ctx, f"{pos} is an incorrect index !\n"
                              f"Your index must be between 1 and {len(queue.players)}.")
        raise PassException()


async def get_picked_player(ctx, mode, queue, name):
    if not name.isdigit():
        return await get_player_by_mention(ctx, mode, name)
    else:
        return await get_player_on_queue(ctx, queue, int(name))


async def get_total_sec(ctx, time, unity):
    formats = {"s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24}
    if not time.isdigit() or unity not in formats.keys():
        await send_error(ctx, "Your ban was incorrectly set\n" +
                         f"Time must be a positive integer, currently it is {time}.\n" +
                         f"Unity must be something in s, m, h, d (secs, mins, hours, days)")
        raise PassException()
    return int(time) * formats[unity]


async def get_captain_team(ctx, queue, mode, captain_id):
    captain = await get_player_by_id(ctx, mode, captain_id)
    team_id = await queue.get_captain_team(ctx, captain)
    team_length = (0, len(queue.red_team), len(queue.blue_team))
    l_oth = team_length[1 if team_id == 2 else 2]
    l_my = team_length[team_id]

    if not ((l_oth == l_my and team_id == 1) or (l_oth > l_my)):
        await send_error(ctx, "It is not your turn to pick.")
        raise PassException()
    return team_id


def get_channel_mode(ctx):
    return f"{ctx.channel.name.split('vs')[0]}" \
           f"{ctx.channel.category.name[0].lower()}"
