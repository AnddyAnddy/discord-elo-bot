import requests
from discord import Embed


def is_url_image(url):
    """Return True if the url is an existing image."""
    img_formats = ('image/png', 'image/jpeg', 'image/jpg')
    req = requests.head(url)
    return "content-type" in req.headers and req.headers["content-type"] in img_formats


def team_name(id_team):
    """Return the name of the team from its id."""
    return ('Nobody', 'Red', 'Blue')[id_team]


def list_to_int(list_str):
    """Return the list but every elem is converted to int."""
    return [int(elem) for elem in list_str]


def get_elem_from_embed(reaction):
    mb = reaction.message.embeds[0]
    footer = mb.footer.text.split()

    return {
        "current_page": int(footer[1]),
        "last_page": int(footer[3]),
        "function": mb.fields[0].value,
        "key": mb.fields[1].value,
        "mode": int(mb.fields[2].value),
        "id": int(mb.fields[3].value) if len(mb.fields) == 4 else None
    }


def get_startpage(reaction, embed):
    allowed_emojis = {"⏮️": 1, "⬅️": embed["current_page"] - 1,
                      "➡️": embed["current_page"] + 1, "⏭️": embed["last_page"]}
    return allowed_emojis[reaction.emoji]


def add_attribute(game, attr_name, value):
    """Add an attribute to every player when I manually update."""
    for mode in game.leaderboards:
        for player in game.leaderboards[mode]:
            if not hasattr(game.leaderboards[mode][player], attr_name):
                setattr(game.leaderboards[mode][player], attr_name, value)


def reset_attribute(game, attr_name, value):
    """Add an attribute to every player when I manually update."""
    for mode in game.leaderboards:
        for player in game.leaderboards[mode]:
            setattr(game.leaderboards[mode][player], attr_name, value)


def build_other_page(bot, game, reaction, user):
    reaction.emoji = str(reaction)
    if user.id == bot.user.id or not reaction.message.embeds \
            or reaction.emoji not in "⏮️⬅️➡️⏭️":
        return
    embed = get_elem_from_embed(reaction)

    if embed["function"] not in ["leaderboard", "archived", "undecided", "canceled", "commands", "ranks", "history", "most"]:
        return None

    startpage = get_startpage(reaction, embed)
    if embed["function"] == "leaderboard":
        return game.leaderboard(embed["mode"], embed["key"],
                               startpage)
    elif embed["function"] in ["archived", "undecided", "canceled"]:
        return getattr(game, embed["function"])(embed["mode"],
                                               startpage=startpage)
    elif embed["function"] == "history":
        return getattr(game, embed["function"])(embed["mode"],
            embed["id"], startpage=startpage)

    elif embed["function"] == "commands":
        return cmds_embed(bot, startpage)

    elif embed["function"] == "most":
        return most_stat_embed(game, embed["mode"], embed["id"], int(embed["key"]), startpage)
    elif embed["function"] == "ranks":
        return game.display_ranks(embed["mode"], startpage)

    return None



def check_if_premium(game, before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(
            role for role in after.roles if role not in before.roles)
        role_name = new_role.name.lower().split()
        nb_games = 0
        if "double" in role_name:
            nb_games = int(role_name[0])

        for mode in game.available_modes:
            if after.name in game.leaderboards[mode]:
                player = game.leaderboards[mode][after.name]
                player.double_xp = nb_games

        return nb_games
    return False


def cmds_embed(bot, startpage=1):
    nb_pages = 1 + len(bot.commands) // 15
    nl = '\n'
    return Embed(color=0x00FF00, description=\
          '```\n' +\
         '\n'.join([f'{command.name:15}: {command.help.split(nl)[0]}'
            for command in sorted(bot.commands, key=lambda c: c.name)[15 * (startpage - 1): 15 * startpage]
            if command.help is not None and not command.hidden]) + '```')\
            .add_field(name="name", value="commands") \
            .add_field(name="-", value="-") \
            .add_field(name="-", value=0) \
            .set_footer(text=f"[ {startpage} / {nb_pages} ]")


def most_stat_embed(game, mode, id, order_key=1, startpage=1):
    most_played_with = build_most_played_with(game, mode, id)
    len_page = 20
    nb_pages = 1 + len(most_played_with) // len_page
    cpage = len_page * (startpage - 1)
    npage = len_page * startpage
    return Embed(title="Stat of most played with players leaderboard",
        color=0x00FF00,
        description=\
        f'```\n{"name":20} {"with":7} {"draw":7} {"wins":7} {"losses":7}\n' +\
        '\n'.join([
            f"{name:20} {_with:<7} {d:<7} {w:<7} {l:<7}"
            for name, (_with, d, w, l) in sorted(most_played_with.items(),
                key=lambda x: x[order_key], reverse=True)[cpage: npage]]) +
            "```"
        ).add_field(name="name", value="most") \
        .add_field(name="key", value=order_key - 1) \
        .add_field(name="mode", value=mode) \
        .add_field(name="id", value=id) \
        .set_footer(text=f"[ {startpage} / {nb_pages} ]")


def get_player_lb_pos(leaderboard, player, key):
    """Return the player position in the leaderboard based on the key O(n)."""
    res = 1
    for _, p in leaderboard.items():
        res += getattr(p, "elo") > getattr(player, "elo")
    return res

def build_most_played_with(game, mode, name):
    most_played_with = {}
    archive = game.archive[mode]
    player = game.leaderboards[mode][name]
    for (queue, win, _) in archive.values():
        if player in queue:
            team = queue.red_team if player in queue.red_team else queue.blue_team
            for p in team:
                team_players_stats(p, player, most_played_with, win, queue)
    most_played_with.pop(player.name, None)
    return most_played_with

def team_players_stats(team_player, me, most_played_with, win, queue):
    if team_player.name in most_played_with:
        most_played_with[team_player.name][0] += 1
    else:
        # nb matches with, nb draws, nb wins, nb losses
        most_played_with[team_player.name] = [1, 0, 0, 0]
    if win == 0:
        most_played_with[team_player.name][1] += 1
    elif queue.player_in_winners(win, me):
        most_played_with[team_player.name][2] += 1
    else:
        most_played_with[team_player.name][3] += 1
