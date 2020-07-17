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


async def get_player(ctx, mode, mention):
    """Return the player from the leaderboard if exists or raise IncorrectName."""
    # Mention is a string in the <@long_number_id> format
    id = mention[3: -1]
    game = get_game(ctx)
    if id.isdigit() and int(id) in game.leaderboards[mode]:
        return game.leaderboards[mode][int(id)]

    await send_error(ctx, IncorrectName(mention))
    raise PassException()
