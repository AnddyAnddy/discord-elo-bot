from GAMES import GAMES
from discord import Embed




class IncorrectName(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Incorrect argument:\n" +\
            f"You wrote {self.name} but it is not in my data.\n" +\
            "You need to mention the user (ex: @Anddy) and be sure that " +\
            "this user is on the leaderboard."


class PassException(Exception):
    pass


async def send_error(ctx, desc):
    await ctx.send(embed=Embed(title="Error !", color=0x000000, description=str(desc)))
    await ctx.send_help(ctx.invoked_with)


def get_game(ctx):
    """Return the game corresponding to the context's guild."""
    return GAMES[ctx.guild.id]



async def get_player_by_id(ctx, mode, id):
    game = get_game(ctx)
    if str(id).isdigit() and int(id) in game.leaderboards[mode]:
        return game.leaderboards[mode][int(id)]

    await send_error(ctx, IncorrectName(mention))
    raise PassException()


async def get_player_by_mention(ctx, mode, mention):
    """Return the player from the leaderboard if exists or raise IncorrectName."""
    # Mention is a string in the <@long_number_id> format
    id = mention[3: -1]
    return await get_player_by_id(ctx, mode, id)


async def get_id(ctx, mention):
    id = mention[3: -1]
    if id.isdigit() and int(id):
        return int(id)

    await send_error(ctx, IncorrectName(mention))
    raise PassException()



async def get_total_sec(ctx, time, unity):
    formats = {"s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24}
    if not time.isdigit() or unity not in formats.keys():
        await send_error(ctx, "Your ban was incorrectly set\n" +\
            f"Time must be a positive integer, currently it is {time}.\n" +
            f"Unity must be something in s, m, h, d (secs, mins, hours, days)")
        raise PassException()
    return int(time) * formats[unity]
