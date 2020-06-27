"""A class for a guild."""
import operator
import _pickle as pickle
from player import Player
from queue_elo import Queue
from queue_elo import team_to_player_name

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

    def add_archive(self, mode, id, winner):
        """Archive a game."""
        if mode not in self.available_modes:
            return "Mode isn't in available modes, check !modes"
        if id not in self.undecided_games[mode]:
            return "Id of the game isn't in undecided games, check !u [mode]"
        if winner not in (1, 2):
            return "The winner must be 1 (red) or 2 (blue)"
        queue = self.undecided_games[mode][id]
        self.archive[mode][queue.game_id] = (queue, winner)
        self.undecided_games[mode].pop(queue.game_id, None)
        return "The game has been submitted, thanks !"

    def add_game_to_be_played(self, queue):
        """Add a game to undecided games."""
        mode = queue.max_queue / 2
        last_id = self.queues[mode].game_id
        self.undecided_games[mode][last_id] = queue
        self.queues[mode] = Queue(2 * mode, queue.mode, last_id)
        return "The teams has been made, a new queue is starting!"

    def cancel(self, mode, id):
        """Cancel the game and return true if it was correctly cancelded."""
        last_id = self.queues[mode].game_id
        if id == last_id:
            self.queues[mode] = Queue(
                2 * mode, self.queues[mode].mode, last_id)
            return True
        return self.undecided_games[mode].pop(id, None) is not None

    def undecided(self, mode):
        """Return string of undecided game ids."""
        return "```" + \
            '\n - '.join([f"Id: {str(id)}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)}"
                for id, queue in self.undecided_games[mode].items()]) + \
            "\n```"

    def archived(self, mode):
        return "```" + \
            '\n - '.join([f"Id: {str(id)}, \
Winner: Team {'Red' if winner == 1 else 'Blue'}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)}"
            for id, (queue, winner) in self.archive[mode].items()]) + \
            "\n```"


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

    def all_games(self, mode):
        res = "```\n"
