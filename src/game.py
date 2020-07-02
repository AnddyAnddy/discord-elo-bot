"""A class for a guild."""
import operator
import _pickle as pickle
import time
from threading import Timer
from player import Player
from queue_elo import Queue
from queue_elo import team_to_player_name
from elo import Elo
from ban import Ban

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
{'Red' if winner == 1 else 'Blue'} won the game with +{abs(self.elo.red_rating)}."

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
        """Cancel the game and return true if it was correctly cancelded."""
        last_id = self.queues[mode].game_id
        if id == last_id:
            self.queues[mode] = Queue(
                2 * mode, self.queues[mode].mode, last_id)
            return True
        return self.undecided_games[mode].pop(id, None) is not None

    def undecided(self, mode):
        """Return string of undecided game ids."""
        return "```\n - " + \
            '\n - '.join([f"Id: {str(id)}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)}"
                for id, queue in self.undecided_games[mode].items()]) + \
            "\n```"

    def archived(self, mode):
        return "```\n - " + \
            '\n - '.join([f"Id: {str(id)}, \
Winner: Team {'Red' if winner == 1 else 'Blue'}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)}"
            for id, (queue, winner, elo_boost) in self.archive[mode].items()]) + \
            "\n```"

    def get_history(self, mode, player):
        """Return the string showing the history of the chosen mode."""
        return "```\n - " + \
            '\n - '.join([f"Id: {str(id)}, \
Winner: Team {'Red' if winner == 1 else 'Blue'}, \
Red team: {team_to_player_name(queue.red_team)}, \
Blue team: {team_to_player_name(queue.blue_team)}"
            for id, (queue, winner) in self.archive[mode].items() \
                if player in queue.red_team or player in queue.blue_team]) + \
            "\n```"


    def leaderboard(self, mode, key="elo"):
        """Return the string showing the leaderboard of the chosen mode."""
        if mode not in self.available_modes:
            return "Empty leaderboard."

        res = '```\n'
        if key not in Player.STATS:
            res += "Argument not found so imma show you the elo lb !\n - "
        if key == "wlr":
            res += "Only showing > 20 games played for wlr leaderboard"

        i = 1
        lst = sorted(self.leaderboards[mode].values(), reverse=True, key=operator.attrgetter(key))[:20]
        for v in lst:
            if v.nb_matches > 20 and key == "wlr":
                res += f'{i}) {v.name:<15}: {getattr(v, key):.2f}\n'
                i += 1
            elif key != "wlr":
                res += f'{i}) {v.name:<15}: {getattr(v, key)}\n'
                i += 1


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
        return "```\n - " + '\n - '.join([str(p) for p in self.bans.values()]) + "```"
