"""Player class."""
import itertools


class Player():
    """Docstring for Player."""

    STATS = ["name", "elo", "wins", "losses", "nb_matches", "wlr",
             "most_wins_in_a_row", "most_losses_in_a_row",
             "current_win_streak", "current_lose_streak", "double_xp"]
    newid = itertools.count()

    def __init__(self, name, id_user):
        """Init."""
        self.name = name
        self.id_player = next(Player.newid)
        self.id_user = id_user
        self.wins = 0
        self.losses = 0
        self.wlr = 0
        self.nb_matches = 0
        self.elo = 1000
        self.most_wins_in_a_row = 0
        self.most_losses_in_a_row = 0
        self.current_win_streak = 0
        self.current_lose_streak = 0
        self.double_xp = 0
        self.time_ban = 0

    def set_elo(self, new_value):
        """Set the new value to the elo attribute."""
        old = self.elo
        self.elo = new_value
        return old

    def update(self, elo_boost, winner, undo = 1):
        """Update the player's stats after a game.

        undo: if set to -1, the stats earning are reversed, useful to
        undo a game without writing twice this function."""
        elo_boost = 2 * elo_boost if self.double_xp and winner else elo_boost
        self.elo += (elo_boost * undo)
        self.wins += winner * undo
        self.current_win_streak += winner * undo if winner else 0
        self.current_lose_streak += (not winner) * undo if not winner else 0
        self.losses += (not winner) * undo
        self.nb_matches += 1 * undo
        self.double_xp -= (1 * undo) * (self.double_xp > 0)
        self.wlr = self.wins if self.losses == 0 else self.wins / self.losses
        if winner and self.current_win_streak > self.most_wins_in_a_row:
            self.most_wins_in_a_row += 1 * undo
        if not winner and self.current_lose_streak > self.most_losses_in_a_row:
            self.most_wins_in_a_row += 1 * undo


    def __str__(self):
        """Print all attributes of the player."""
        return '```\n' + \
            '\n - '.join([f'{stat}: {getattr(self, stat)}'
                for stat in Player.STATS]) + '```'
