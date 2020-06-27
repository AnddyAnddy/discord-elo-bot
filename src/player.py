"""Player class."""
import itertools


class Player():
    """Docstring for Player."""

    STATS = ["name", "elo", "wins", "losses", "nb_matches", "wlr",
             "most_wins_in_a_row", "most_losses_in_a_row",
             "current_win_streak", "current_lose_streak"]
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
        self.current_win_streak = 0
        self.current_lose_streak = 0

    def set_elo(self, new_value):
        """Set the new value to the elo attribute."""
        old = self.elo
        self.elo = new_value
        return old

    def update(self, elo_boost, winner):
        """Update the player's stats after a game."""
        self.elo += elo_boost
        self.wins += winner
        self.current_win_streak += winner
        self.losses += not winner
        self.nb_matches += 1
        self.wlr = 0 if self.losses == 0 else self.wins / self.losses
        if winner and self.current_win_streak > self.most_wins_in_a_row:
            self.most_wins_in_a_row += 1
        if not winner and self.current_lose_streak > self.most_losses_in_a_row:
            self.most_wins_in_a_row += 1


    def __str__(self):
        """Print all attributes of the player."""
        return '```\n' + \
            '\n - '.join([f'{stat}: {getattr(self, stat)}'
                for stat in Player.STATS]) + '```'
