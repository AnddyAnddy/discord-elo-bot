"""A class for a guild."""
import _pickle as pickle
import operator
import time

from discord import Embed
from emoji import UNICODE_EMOJI

from src.modules.ban import Ban
from src.modules.elo import Elo, undo_elo
from src.modules.player import Player
from src.modules.queue_elo import Queue
from src.modules.queue_elo import team_to_player_name
from src.utils.utils import team_name, split_with_numbers
DEBUG_UNTIL_BETTER = []

class Game:
    """Represent the game available."""

    def __init__(self, guild_id):
        """Initialize a game for a guild."""
        self.guild_id = guild_id
        self.available_positions = []
        self.archive = {}
        self.leaderboards = {}
        self.tmp_leaderboards = {}
        self.limit_leaderboards = 10
        self.undecided_games = {}
        self.cancels = {}
        self.queues = {}
        self.bans = {}
        self.waiting_for_approval = {}
        self.correctly_submitted = {}
        self.ranks = {}  # {modeK: {nameN: RankX, nameN+1: RankY}}
        self.maps_archive = {}  # {modeK: {idN: MapX, idN+1: MapY}}
        self.available_maps = {}  # {nameN: emojiN, nameK: emojiK}
        self.map_pick_mode = 0
        self.date_premium_end = 0
        self.elo = Elo()

    def get_leaderboards(self):
        if not hasattr(self, "limit_leaderboards"):
            setattr(self, "limit_leaderboards", 10)
            setattr(self, "tmp_leaderboards", {})
        return self.tmp_leaderboards if self.limit_leaderboards == 10 else self.leaderboards

    @property
    def available_modes(self):
        """Return the available modes of this guild."""
        if not hasattr(self, "limit_leaderboards"):
            setattr(self, "limit_leaderboards", 10)
            setattr(self, "tmp_leaderboards", {})
        return self.tmp_leaderboards.keys() if self.limit_leaderboards == 10 else self.leaderboards.keys()


    def leaderboard(self, mode):
        """Return leaderboard depending on whether the guild is premium."""
        # doing that for retro compatibility issues
        if not hasattr(self, "limit_leaderboards"):
            setattr(self, "limit_leaderboards", 10)
            setattr(self, "tmp_leaderboards", {})
        if self.limit_leaderboards == 10:
            if mode not in self.tmp_leaderboards:
                if mode in self.leaderboards:
                    DEBUG_UNTIL_BETTER.append(True)

                raise ValueError(f"Mode ({mode}) not in leaderboard ({self.tmp_leaderboards.keys()})")
            return self.tmp_leaderboards[mode]
        if mode not in self.leaderboards:
            raise ValueError(f"Mode ({mode}) not in leaderboard ({self.tmp_leaderboards.keys()})")
        return self.leaderboards[mode]

    def add_archive(self, mode, id, winner):
        """Archive a game."""
        if mode not in self.available_modes:
            return "Mode isn't in available modes, check !modes", False
        if id not in self.undecided_games[mode]:
            return "Id of the game isn't in undecided games, check !u [mode]", False
        if winner not in range(3):
            return "The winner must be 0(draw), 1 (red) or 2 (blue)", False
        queue = self.undecided_games[mode][id]
        self.elo.update(queue, winner)
        self.archive[mode][queue.game_id] = (
            queue, winner, self.elo.red_rating)
        self.undecided_games[mode].pop(queue.game_id, None)
        return f"The game n°{id} was submitted, thanks !\n" \
               f"{team_name(winner)} won the game.\n" \
               f"Red bonus: {self.elo.red_rating if winner else 0}, \n" \
               f"Blue bonus: {self.elo.blue_rating if winner else 0}.", True

    def undo(self, mode, id):
        """Undo a game."""
        game = self.archive[mode].pop(id, None)
        if game is None:
            return "The game couldn't be found"
        self.undecided_games[mode][id] = game[0]
        undo_elo(game[0], game[1], game[2])
        return f"The game has been undone, the stats got canceled " \
               f"{game[2]} elo points canceled."

    def add_game_to_be_played(self, queue, mode):
        """Add a game to undecided games."""
        last_id = self.queues[mode].game_id
        self.undecided_games[mode][last_id] = queue
        self.queues[mode] = Queue(2 * int(split_with_numbers(mode)[0]),
                                  queue.mode, queue.map_mode, last_id)
        return "The teams have been made, a new queue is starting!"

    def cancel(self, mode, id):
        """Cancel the game and return true if it was correctly canceled."""
        last_id = self.queues[mode].game_id
        if id == last_id:
            if not hasattr(self.queues[mode], "map_mode"):
                setattr(self.queues[mode], "map_mode", 0)
            self.queues[mode] = Queue(
                2 * int(split_with_numbers(mode)[0]), self.queues[mode].mode,
                self.queues[mode].map_mode, last_id)
            return True
        res = self.undecided_games[mode].pop(id, None)
        if res is None:
            return False
        # self.cancels[mode][id] = res
        return True

    def uncancel(self, mode, id):
        """Remove the game to cancel and put it in undecided.

        Slightly similar to undo"""
        game = self.cancels[mode].pop(id, None)
        if game is None:
            return "The game couldn't be found"
        self.undecided_games[mode][id] = game
        return "The game has been uncanceled"

    def embed_canceled(self, mode, start_page=1):
        """Return an embed of all canceled games."""
        nb_pages = 1 + len(self.cancels[mode]) // 20

        return Embed(color=0x00FF00,
                     description="```\n - " + '\n - '.join([f"Id: {str(id)}"
                                                            for id in sorted(self.cancels[mode])
                                                            [20 * (start_page - 1): 20 * start_page]]) + "```") \
            .add_field(name="name", value="canceled") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def embed_undecided(self, mode, start_page=1):
        """Return string of undecided game ids."""
        nb_pages = 1 + len(self.undecided_games[mode]) // 25
        return Embed(color=0x00FF00,
                     description=f"\n```{'Id':5} {'Red captain':20} {'Blue captain':20}\n"
                                 + '\n'.join([f"{str(id):5} "
                                              f"{queue.red_team[0].name:20} "
                                              f"{queue.blue_team[0].name:20}"
                                              for id, queue in sorted(self.undecided_games[mode].items())
                                              [25 * (start_page - 1): 25 * start_page] if queue.red_team]) + "```") \
            .add_field(name="name", value="undecided") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def embed_archived(self, mode, start_page=1):
        len_page = 25
        nb_pages = 1 + len(self.archive[mode]) // len_page
        current_page = len_page * (start_page - 1)
        next_page = len_page * start_page
        return Embed(color=0x00FF00,
                     description=f"\n```{'Id':5} {'Winner':8} {'Red captain':20} {'Blue captain':20}\n"
                                 + '\n'.join([f"{str(id):5} "
                                              f"{team_name(winner):8} "
                                              f"{queue.red_team[0].name:20} "
                                              f"{queue.blue_team[0].name:20}"
                                              for id, (queue, winner, elo_boost) in
                                              sorted(self.archive[mode].items())[current_page:next_page]]) +
                                 "\n```") \
            .add_field(name="name", value="archived") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def embed_history(self, mode, player, start_page=1):
        """Return the string showing the history of the chosen mode."""
        len_page = 10
        current_page = len_page * (start_page - 1)  # current page
        next_page = len_page * start_page  # next page
        history = [(id, (queue, winner, elo)) for (id, (queue, winner, elo))
                   in self.archive[mode].items() if player in queue]
        nb_pages = 1 + len(history) // len_page
        return Embed(color=0x00FF00,
                     description=f'```\n{"Id":4} {"Win":3} {"Red team":^44} {"Elo":3}\n'
                                 f'{" ":8} {"Blue team":^44}\n{"_" * 58}\n'
                                 + f"{'_' * 58}\n".join([f"{str(id):4} "
                                                         f"{winner:3} "
                                                         f"{team_to_player_name(queue.red_team):^44} "
                                                         f"{abs(elo)}\n"
                                                         f"{' ':8} {team_to_player_name(queue.blue_team):^44} "
                                                         for id, (queue, winner, elo) in
                                                         history[current_page:next_page]]) +
                                 "\n```") \
            .add_field(name="name", value="history") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .add_field(name="id", value=player.id_user) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def embed_leaderboard(self, mode, key="elo", start_page=1):
        """Return the string showing the leaderboard of the chosen mode."""
        res = '```\n'
        if key not in Player.STATS:
            res += "Argument not found so imma show you the elo lb !\n"
            key = "elo"
        if key == "wlr":
            res += "Only showing > 20 games played for wlr leaderboard\n"

        lst = sorted(self.leaderboard(mode).values(),
                     reverse=True,
                     key=operator.attrgetter(key))

        i = 20 * (start_page - 1)
        index = i
        end = 20 * start_page
        while i < end and i < len(lst) and index < len(lst):
            v = lst[index]
            if v.nb_matches > 20 and key == "wlr":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {getattr(v, key):.2f}\n'
                i += 1
            elif key == "last_join":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {getattr(v, key).strftime("%d/%m/%Y")}\n'
                i += 1

            elif key != "wlr":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {str(getattr(v, key)):>10}\n'
                i += 1

            index += 1

        res += '```'
        nb_pages = 1 + len(self.leaderboard(mode)) // 20

        return Embed(color=0x00AAFF,
                     title=f"**Elo by Anddy {mode}vs{mode} leaderboard**",
                     description=res)\
            .add_field(name="name", value="leaderboard") \
            .add_field(name="key", value=key) \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def add_mode(self, mode):
        """Add the mode in the set."""
        if mode in self.available_modes:
            return False
        if not hasattr(self, "tmp_leaderboards"):
            setattr(self, "tmp_leaderboards", {})
        if self.limit_leaderboards == 10:
            self.tmp_leaderboards[mode] = {}
        else:
            self.leaderboards[mode] = {}
        self.undecided_games[mode] = {}
        self.archive[mode] = {}
        self.ranks[mode] = {}
        self.cancels[mode] = {}

        # self.bans = {}
        pick_mode = 0 if split_with_numbers(mode)[1] == 's' else 6
        self.queues[mode] = Queue(2 * int(split_with_numbers(mode)[0]), pick_mode, 0)
        return True

    def remove_mode(self, mode):
        """Totally delete the mode in the data."""
        self.get_leaderboards().pop(mode)
        self.queues.pop(mode)
        self.undecided_games.pop(mode, None)

    def save_to_file(self):
        """Save the whole class in it's data/guild_id file."""
        with open(f'./data/{self.guild_id}.data', "wb") as outfile:
            pickle.dump(self, outfile, -1)
        with open(f'./data2/{self.guild_id}.data', "wb") as outfile:
            pickle.dump(self, outfile, -1)

    def unban_player(self, name):
        """Unban a player."""
        self.bans.pop(name, None)

    def ban_player(self, name, time_left, reason=""):
        """Ban the player for a certain time in seconds."""
        self.bans[name] = Ban(name, time_left, reason)
        self.erase_player_from_queues(name)

    def erase_player_from_queues(self, name):
        """Remove the player from every queues if the queue hasn't been full."""
        for mode in self.queues:
            if name in self.leaderboard(mode):
                self.queues[mode].remove_player(self.leaderboard(mode)[name])

    def erase_player_from_leaderboards(self, name):
        """Remove the player from every leaderboards."""
        for mode in self.get_leaderboards():
            self.leaderboard(mode).pop(name, None)

    def all_bans(self):
        """Show the list of every banned person."""
        return "\n - " + '\n - '.join([str(p) for p in self.bans.values()])

    def remove_negative_bans(self):
        """Remove every bans where the time has been reached without thread."""
        t = time.time()
        self.bans = {
            id: player for id, player in self.bans.items()
            if t < player.time_end
        }

    def set_elo(self, mode, name, elo):
        if name in self.leaderboard(mode):
            self.leaderboard(mode)[name].elo = elo

    def redo_all_games(self):
        """Undo every games that ever happened and redo them."""
        for mode in self.archive:
            for id in list(self.archive[mode])[::-1]:
                queue, winner, elo = self.archive[mode][id]
                self.undo(mode, id)
                self.add_archive(mode, id, winner)

    def get_game(self, mode, id):
        """Try to find the game in archived, undecided or canceled dict."""
        if id in self.archive[mode]:
            return self.archive[mode][id], 0
        if id in self.cancels[mode]:
            return self.cancels[mode][id], 1
        if id in self.undecided_games[mode]:
            return self.undecided_games[mode][id], 2
        return None, -1

    def get_rank_url(self, mode, elo_points, player):
        """Return the url corresponding to the elo rank."""
        if player.double_xp > 0:
            return "https://i.imgur.com/IBWHO8G.png"
        for name, rank in self.ranks[mode].items():
            if elo_points in rank.range:
                return rank.url
        return ""

    def get_rank_name(self, mode, elo_points, player):
        """Return the name corresponding to the elo rank."""
        if player.double_xp > 0:
            return "Premium"
        if player.nb_matches < 20:
            return "Unranked (20 games needed)"
        for name, rank in self.ranks[mode].items():
            if elo_points in rank.range:
                return ' '.join(split_with_numbers(name)) + \
                       f" ({rank.start()} - {rank.stop()})"
        return "Unranked"

    def update_ranks(self, mode):
        """Adapt the range of the ranks to keep a 1/10 spread."""
        pass

    def display_ranks(self, mode, start_page=1):
        """Return a string showing every ranks of a specific mode."""
        nb_pages = 1 + len(self.ranks[mode]) // 20
        return Embed(color=0x00FF00,
                     description=f'```{"Name":15} {"Start":5} {"Stop":5}\n'
                                 + '\n'.join([
                         f"{rank.name:15} "
                         f"{rank.start():5} "
                         f"{rank.stop():5}"
                         for name, rank in sorted(self.ranks[mode].items(),
                                                  key=lambda r: r[1].start())
                         [20 * (start_page - 1): 20 * start_page]])
                                 + "```") \
            .add_field(name="name", value="ranks") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def add_map(self, emoji, name):
        """Add the map in the available maps."""
        if emoji not in UNICODE_EMOJI:
            return "The emoji couldn't be found."
        if name in self.available_maps or emoji in self.available_maps.values():
            return "The map couldn't been added because the name or the emoji already exists."

        self.available_maps[name] = emoji
        return f"{emoji} {name} was correctly added !"

    def delete_map(self, name):
        """Delete the map from the available maps."""
        if name not in self.available_maps:
            return f"The map does not exist with that name {name}, check !maps"
        emoji = self.available_maps.pop(name, None)
        return f"{emoji} {name} was correctly removed from the maps."

    def embed_maps(self, start_page=1):
        """Return the available_maps."""
        len_page = 25
        nb_pages = 1 + len(self.available_maps) // len_page
        current_page = len_page * (start_page - 1)
        next_page = len_page * start_page
        return Embed(title="Maps",
                     color=0x00FF00,
                     description="```\n" +
                                 '\n'.join([f"{emoji} {name:50} " for name, emoji in
                                            sorted(self.available_maps.items())[current_page:next_page]])
                                 + "```"
                     ) \
            .add_field(name="name", value="maps") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=0) \
            .set_footer(text=f"[ {start_page} / {nb_pages} ]")

    def add_map_to_archive(self, mode, id, name, emoji):
        """Add the map to the map to the played maps.

        Called on game announce."""
        self.maps_archive[mode][id] = (name, emoji)

    def delete_map_from_archive(self, mode, id):
        """Delete the map from the played maps.

        Called on game cancel."""
        self.maps_archive[mode].pop(id, None)

    def embed_lobby_maps(self, mode, id):
        if isinstance(self.maps_archive[mode][id], tuple):
            name, emoji = self.maps_archive[mode][id]
            return Embed(color=0x00FF00,
                         title="Only one map",
                         description=f"The bot randomly picked the map ** {emoji} {name}**")
        return Embed(title="Lobby maps",
                     color=0x00FF00,
                     description="```\n" +
                                 '\n'.join([f"{str(emoji)} {name:40} "
                                            for name, emoji in self.maps_archive[mode][id]]) +
                                 "\n```" +
                                 f"We need **{2 * int(split_with_numbers(mode)[0]) + 1}** total votes or a map getting "
                                 f"**{int(split_with_numbers(mode)[0]) + 2}** votes to keep going!"
                     ) \
            .add_field(name="name", value="lobby_maps") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .add_field(name="id", value=id) \
            .set_footer(text=f"[ 1 / 1 ]")

    def get_last_undecided_game_by(self, player, mode):
        """Return the id of the last played game by a specific player."""
        if player.id_user not in self.leaderboard(mode):
            return None

        for id, queue in sorted(self.undecided_games[mode].items(), key=lambda x: x, reverse=True):
            if player in queue:
                return queue
        return None

    def clear_undecided_reacted(self):
        """Used on ready to clear the undecided games reactions.

        Because the bot doesn't parse old (before on ready) messages it can't
        know if a user reacted.
        """
        for mode in self.available_modes:
            for queue in self.undecided_games[mode].values():
                queue.clear_reacted()

    def check_for_premium(self):
        """Remove the premium if the date is over the ending premium date."""
        if not hasattr(self, "date_premium_end"):
            setattr(self, "date_premium_end", 0)
        if time.time() >= self.date_premium_end:
            self.limit_leaderboards = 10
            self.date_premium_end = 0
