"""Player class."""
import itertools


class Player():
    """Docstring for Player."""

    STATS = ["name", "elo", "wins", "losses", "nb_matches", "wlr",
             "most_wins_in_a_row", "most_losses_in_a_row"]
    newid = itertools.count()

    def __init__(self, name):
        """Init."""
        self.name = name
        self.id_player = next(Player.newid)
        self.wins = 0
        self.losses = 0
        self.wlr = 0
        self.nb_matches = 0
        self.elo = 1000
        self.most_wins_in_a_row = 0
        self.most_losses_in_a_row = 0

    def set_elo(self, new_value):
        """Set the new value to the elo attribute."""
        old = self.elo
        self.elo = new_value
        return old

    def __str__(self):
        """Print all attributes of the player."""
        return '```\n' + \
            '\n - '.join([f'{stat}: {getattr(self, stat)}'
                for stat in Player.STATS]) + '```'
