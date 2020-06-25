"""Simulation of queue."""
from random import shuffle


class Queue():
    """Docstring for Queue."""
    QUEUE_ID = 0
    RANDOM_TEAM = 0
    BALANCED_RANDOM = 1
    TOP_CAP = 2
    RANDOM_CAP = 3

    def __init__(self, max_queue, mode):
        """Initialize the queue."""
        if max_queue < 2 or max_queue % 2 == 1:
            raise ValueError("The max queue must be an even number > 2")
        if not 0 <= mode <= 3:
            raise ValueError("The mode is not correct: [0, 1, 2, 3] = \
[random teams, balanced random, highest rank cap, rank cap]")
        self.players = []
        self.red_team = []
        self.blue_team = []
        self.max_queue = max_queue
        self.has_queue_been_full = False
        self.modes = [self.random_team, self.balanced_random]
        self.pick_fonction = self.modes[mode]
        self.game_id = Queue.QUEUE_ID
        Queue.QUEUE_ID += 1

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
        res = f'{player.name} has been added to the queue'
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
        if not self.is_queue_full():
            return
        self.has_queue_been_full = True
        self.pick_fonction()
        game.add_game_to_be_played(self)
        return message_on_queue_full(self.players, self.red_team, self.blue_team)

    def is_queue_finished(self):
        """Create new queue after the previous one was completed."""
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

    def __str__(self):
        """ToString."""
        if not self.has_queue_been_full:
            return display_team(self.players, "Queue")
        return message_on_queue_full(self.players,
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


HISTORIQUE = []
if __name__ == '__main__':
    import doctest
    doctest.testfile("../test/queue.txt")
