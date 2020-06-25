"""A class for a guild."""
import operator
import _pickle as pickle
from player import Player
from queue_elo import Queue


class Game():
    """Represent the game available."""

    def __init__(self, guild_id):
        """Initialize a game for a guild."""
        self.guild_id = guild_id
        self.available_modes = set()
        self.archive = {}
        self.leaderboards = {}
        self.undecided_games = {}
        self.queues = {}

    def add_archive(self, queue, winner, mode):
        """Archive a game."""
        self.archive[mode].add({queue.game_id:
                                (queue.red_team, queue.blue_team, winner)})
        self.undecided_games[mode].pop(queue.id, None)

    def add_game_to_be_played(self, queue):
        """Add a game to undecided games."""
        print(self.undecided_games[queue.max_queue / 2])
        self.undecided_games[queue.max_queue / 2][queue.game_id] =\
            (queue.red_team, queue.blue_team)

    def undecided(self, mode):
        """Return string of undecided game ids."""
        return '\n - '.join([game.id for game in self.undecided_games[mode]])

    def leaderboard(self, mode, key="elo"):
        """Return the string showing the leaderboard of the chosen mode."""
        if mode not in self.available_modes:
            return "Empty leaderboard."

        res = '```'
        if key not in Player.STATS:
            res += "Argument not found so imma show you the elo lb !\n"
        res += '\n - '.join([f'{i}) {v.name}: {getattr(v, key)}'
                             for i, v in enumerate(
                                 sorted(self.leaderboards[mode].values(),
                                        key=operator.attrgetter(key)), 1)])
        res += '```'
        return res

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

    def in_modes(self, mode):
        return mode.isdigit() and int(mode) in self.available_modes
