"""Simulation of queue."""
from threading import Timer
from random import shuffle


class Queue():
    """Docstring for Queue."""
    RANDOM_TEAM = 0
    BALANCED_RANDOM = 1
    TOP_CAP = 2
    RANDOM_CAP = 3

    def __init__(self, max_queue, mode, last_id = 0):
        """Initialize the queue."""
        if max_queue < 2 or max_queue % 2 == 1:
            raise ValueError("The max queue must be an even number > 2")
        if not 0 <= mode <= 3:
            raise ValueError("The mode is not correct: [0, 1, 2, 3] = \
[random teams, balanced random, highest rank cap, rank cap]")
        self.players = []
        self.timeout = {}
        self.red_team = []
        self.blue_team = []
        self.max_queue = max_queue
        self.has_queue_been_full = False
        self.modes = [self.random_team, self.balanced_random]
        self.pick_fonction = self.modes[mode]
        self.mode = mode
        self.game_id = last_id + 1

    def is_queue_full(self):
        """Return true if the queue is full."""
        return self.max_queue == len(self.players)

    def add_player(self, player, game):
        """Add a player in the queue."""
        if player in self.players:
            return "You can't join twice, maybe you look for !l"
        if self.is_queue_full() or self.has_queue_been_full:
            return "Queue is full..."
        self.players.append(player)
        self.timeout[player] = Timer(60 * 10, self.remove_player, (player, ))
        self.timeout[player].start()
        res = f'{player.name} has been added to the queue, you will be kicked \
in 10 mins if the queue has not been full.'
        if self.is_queue_full():
            res += "\nQueue is full, let's start the next session.\n"
            res += self.on_queue_full(game)
        return res

    def remove_player(self, player):
        """Remove a player from the queue."""
        if player in self.players and not self.has_queue_been_full:
            self.players.remove(player)
            return f'{player.name} was removed from the queue'
        return f"{player.name} can't be removed from the queue"

    def on_queue_full(self, game):
        """Set a game."""
        self.has_queue_been_full = True
        for t in self.timeout.values():
            t.cancel()
        self.timeout = {}
        self.pick_fonction()
        return f'Game n°{self.game_id}:\n' + message_on_queue_full(self.players,
                                                    self.red_team,
                                                    self.blue_team)

    def is_finished(self):
        """Return true if the teams are full based on the max_queue."""
        return len(self.red_team) == len(self.blue_team) == self.max_queue / 2

    def players_to_teams(self):
        """Set the players to the teams.

        If the mode is random then the list must be randomized first.
        If the mode is balanced then the list must be sorted by elo first.
        """
        while self.players != []:
            self.red_team.append(self.players.pop())
            self.blue_team.append(self.players.pop())

    def random_team(self):
        """Set the teams to random players."""
        shuffle(self.players)
        self.players_to_teams()

    def balanced_random(self):
        """Set the teams to balanced elo."""
        self.players.sort(reverse=True, key=lambda p: p.elo)
        self.players_to_teams()


    def get_captain_team(self, name):
        """Return 1 if red, 2 if blue, 0 if none."""
        red_cap, blue_cap = self.red_team[0], self.blue_team[0]
        for i, p in enumerate([red_cap, blue_cap], start=1):
            if p.name == ctx.author.name:
                return i
        return 0

    def set_player_team(self, team_id, player):
        """Move the player from the players to the team."""
        team = self.red_team if team_id == 1 else self.blue_team
        team.append(self.players.pop(self.players.index(player)))

    def __str__(self):
        """ToString."""
        res = f"Game n°{self.game_id}\n"
        if not self.has_queue_been_full:
            return res + display_team(self.players, "Queue")
        return res + message_on_queue_full(self.players,
                                     self.red_team,
                                     self.blue_team)


def display_team(team, team_name):
    """Show the player list of a specific team."""
    return f'```\n{team_name}\n - ' +\
        '\n - '.join([p.name + ' ' + str(p.elo) for p in team]) +\
        '\n```'


def message_on_queue_full(players, red_team, blue_team):
    """Start the captain menu."""
    string = 'Two captains have been randomly picked !\n'
    string += f'{red_team[0].name} is the red cap\n'
    string += f'{blue_team[0].name} is the blue cap\n'

    string += display_team(red_team, "Red team")
    string += display_team(blue_team, "Blue team")
    string += display_team(players, "Remaining players")
    return string



def team_to_player_name(team):
    return "[" + ' '.join([p.name for p in team]) + "]"

HISTORIQUE = []
if __name__ == '__main__':
    import doctest
    doctest.testfile("../test/queue.txt")
