"""A class for a guild."""
import _pickle as pickle
import operator
import time

from ban import Ban
from discord import Embed
from elo import Elo
from player import Player
from queue_elo import Queue
from queue_elo import team_to_player_name


class Game():
    """Represent the game available."""

    def __init__(self, guild_id):
        """Initialize a game for a guild."""
        self.guild_id = guild_id
        self.available_modes = set()
        self.available_positions = []
        self.archive = {}
        self.leaderboards = {}
        self.undecided_games = {}
        self.cancels = {}
        self.queues = {}
        self.bans = {}
        self.elo = Elo()

    def add_archive(self, mode, id, winner):
        """Archive a game."""
        if mode not in self.available_modes:
            return "Mode isn't in available modes, check !modes"
        if id not in self.undecided_games[mode]:
            return "Id of the game isn't in undecided games, check !u [mode]"
        if winner not in (1, 2):
            return "The winner must be 1 (red) or 2 (blue)"
        queue = self.undecided_games[mode][id]
        self.elo.update(queue, winner)
        self.archive[mode][queue.game_id] = (queue, winner, self.elo.red_rating)
        self.undecided_games[mode].pop(queue.game_id, None)
        return f"The game has been submitted, thanks !\n\
{'Red' if winner == 1 else 'Blue'} won the game.\n\
Red bonus: {self.elo.red_rating}, Blue bonus: {self.elo.blue_rating}."

    def undo(self, mode, id):
        """Undo a game."""
        game = self.archive[mode].pop(id, None)
        if game is None:
            return "The game couldn't be found"
        self.undecided_games[mode][id] = game[0]
        self.elo.undo_elo(game[0], game[1], game[2])
        return "The game has been undone, the stats got canceled"

    def add_game_to_be_played(self, queue):
        """Add a game to undecided games."""
        mode = queue.max_queue / 2
        last_id = self.queues[mode].game_id
        self.undecided_games[mode][last_id] = queue
        self.queues[mode] = Queue(2 * mode, queue.mode, last_id)
        return "The teams have been made, a new queue is starting!"

    def cancel(self, mode, id):
        """Cancel the game and return true if it was correctly canceled."""
        last_id = self.queues[mode].game_id
        if id == last_id:
            self.queues[mode] = Queue(
                2 * mode, self.queues[mode].mode, last_id)
            return True
        res = self.undecided_games[mode].pop(id, None)
        if res is None:
            return False
        self.cancels[mode][id] = res
        return True

    def uncancel(self, mode, id):
        """Remove the game to cancel and put it in undecided.

        Slightly similar to undo"""
        game = self.cancels[mode].pop(id, None)
        if game is None:
            return "The game couldn't be found"
        self.undecided_games[mode][id] = game
        return "The game has been uncanceled"

    def canceled(self, mode, startpage=1):
        """Return an embed of all canceled games."""
        nb_pages = 1 + len(self.archive[mode]) // 20

        return Embed(color=0x00FF00,
                     description= \
                         "```\n - " + '\n - '.join([f"Id: {str(id)}"
                                                    for id in sorted(self.cancels[mode]) \
                                                        [20 * (startpage - 1): 20 * startpage]]) + "```") \
            .add_field(name="name", value="canceled") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {startpage} / {nb_pages} ]")


    def undecided(self, mode, startpage=1):
        """Return string of undecided game ids."""
        nb_pages = 1 + len(self.undecided_games[mode]) // 25

        return Embed(color=0x00FF00,
                     description= \
                         f"\n```{'Id':5} {'Red captain':20} {'Blue captain':20}\n" + \
                         '\n'.join([f"{str(id):5} "
                          f"{queue.red_team[0].name:20} " \
                          f"{queue.blue_team[0].name:20}"
                        for id, queue in sorted(self.undecided_games[mode].items()) \
                            [25 * (startpage - 1): 25 * startpage]]) + "```") \
            .add_field(name="name", value="undecided") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {startpage} / {nb_pages} ]")

    def archived(self, mode, startpage=1):
        nb_pages = 1 + len(self.archive[mode]) // 25

        return Embed(color=0x00FF00,
                     description= \
                         f"\n```{'Id':5} {'Winner':7} {'Red captain':20} {'Blue captain':20}\n" + \
                         '\n'.join([f"{str(id):5} " \
                         f"{'Red' if winner == 1 else 'Blue':7} " \
                         f"{queue.red_team[0].name:20} " \
                         f"{queue.blue_team[0].name:20}"
                           for id, (queue, winner, elo_boost) in
                           sorted(self.archive[mode].items())[25 * (startpage - 1): 25 * startpage]]) + \
                         "\n```")\
            .add_field(name="name", value="archived") \
            .add_field(name="-", value="-") \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {startpage} / {nb_pages} ]")

    def get_history(self, mode, player):
        """Return the string showing the history of the chosen mode."""
        return "```\n - " + \
               '\n - '.join([f"Id: {str(id)}, \
Winner: Team {'Red' if winner == 1 else 'Blue'}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)} \
Elo: {elo}"
                             for id, (queue, winner, elo) in self.archive[mode].items() \
                             if player in queue.red_team or player in queue.blue_team]) + \
               "\n```"

    def leaderboard(self, mode, key="elo", startpage=1):
        """Return the string showing the leaderboard of the chosen mode."""
        if mode not in self.available_modes:
            return "Empty leaderboard."

        res = '```\n'
        if key not in Player.STATS:
            res += "Argument not found so imma show you the elo lb !\n"
            key = "elo"
        if key == "wlr":
            res += "Only showing > 20 games played for wlr leaderboard\n"

        i = 1
        lst = sorted(self.leaderboards[mode].values(),
                     reverse=True,
                     key=operator.attrgetter(key))

        i = 20 * (startpage - 1)
        index = i
        end = 20 * startpage
        while i < end and i < len(lst) and index < len(lst):
            v = lst[index]
            if v.nb_matches > 20 and key == "wlr":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {getattr(v, key):.2f} '
                i += 1
            elif key == "last_join":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {getattr(v, key).strftime("%d/%m/%Y")} '
                i += 1

            elif key != "wlr":
                res += f'{"0" if i < 9 else ""}{i + 1}) {v.name:<20} {str(getattr(v, key)):>10} '
                i += 1
            res += '\n'

            index += 1

        res += '```'
        nb_pages = 1 + len(self.leaderboards[int(mode)]) // 20
        return Embed(color=0x00AAFF,
                     title=f"**Elo by Anddy {mode}vs{mode} leaderboard**",
                     description=res).add_field(name="name", value="leaderboard") \
            .add_field(name="key", value=key) \
            .add_field(name="mode", value=mode) \
            .set_footer(text=f"[ {startpage} / {nb_pages} ]")

    def add_mode(self, mode):
        """Add the mode in the set."""
        if mode in self.available_modes:
            return False
        self.available_modes.add(mode)
        self.leaderboards[mode] = {}
        self.undecided_games[mode] = {}
        self.archive[mode] = {}
        self.queues[mode] = Queue(2 * mode, 0)
        return True

    def remove_mode(self, mode):
        """Totally delete the mode in the data."""
        self.available_modes.discard(mode)
        self.leaderboards.pop(mode)
        self.queues.pop(mode)
        self.undecided_games.pop(mode, None)

    def save_to_file(self):
        """Save the whole class in it's data/guild_id file."""
        with open(f'./data/{self.guild_id}.data', "wb") as outfile:
            pickle.dump(self, outfile, -1)
        with open(f'./data2/{self.guild_id}.data', "wb") as outfile:
            pickle.dump(self, outfile, -1)

    def in_modes(self, mode):
        return mode.isdigit() and int(mode) in self.available_modes

    def unban_player(self, name):
        """Unban a player."""
        self.bans.pop(name, None)

    def ban_player(self, name, time_left, reason=""):
        """Ban the player for a certain time in seconds."""
        self.bans[name] = Ban(name, time_left, reason)
        self.erase_player_from_queues(name)
        # Timer(self.bans[name].time_end - time.time(),
        #         self.unban_player,
        #         (name, )).start()

    def erase_player_from_queues(self, name):
        """Remove the player from every queues if the queue hasn't been full."""
        for mode in self.queues:
            if name in self.leaderboards[mode]:
                self.queues[mode].remove_player(self.leaderboards[mode][name])

    def erase_player_from_leaderboards(self, name):
        """Remove the player from every leaderboards."""
        for mode in self.leaderboards:
            self.leaderboards[mode].pop(name, None)

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
        if name in self.leaderboards[mode]:
            self.leaderboards[mode][name].elo = elo

    def redo_all_games(self):
        """Undo every games that ever happened and redo them."""
        for mode in self.archive:
            for id in list(self.archive[mode])[::-1]:
                queue, winner, elo = self.archive[mode][id]
                self.undo(mode, id)
                self.add_archive(mode, id, winner)
