"""Player class."""
import itertools
from datetime import datetime


class Player:
    """Docstring for Player."""

    STATS = ["name", "elo", "wins", "losses", "nb_matches", "wlr",
             "most_wins_in_a_row", "most_losses_in_a_row",
             "current_win_streak", "current_lose_streak", "double_xp",
             "fav_pos"]
    new_id = itertools.count()

    def __init__(self, name, id_user):
        """Init."""
        self.name = name
        self.id_player = next(Player.new_id)
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
        self.fav_pos = []
        self.last_join = datetime.now()

    def set_elo(self, new_value):
        """Set the new value to the elo attribute."""
        old = self.elo
        self.elo = new_value
        return old

    def fav_pos_str(self):
        return ' '.join([elem for elem in self.fav_pos])

    def draw_update(self, undo=1):
        """Same than update but implementing a draw."""
        self.current_win_streak = 0 if undo == 1 else self.current_win_streak
        self.current_lose_streak = 0 if undo == 1 else self.current_lose_streak
        self.nb_matches += 1 * undo
        self.double_xp -= (1 * undo) * (self.double_xp > 0)

    def win_lose_update(self, elo_boost, winner, undo=1):
        """Update the player's stats after a game.

        undo: if set to -1, the stats earning are reversed, useful to
        undo a game without writing twice this function."""
        elo_boost = 2 * elo_boost + 2 * \
            self.current_win_streak if self.double_xp and winner else elo_boost
        self.elo += (elo_boost * undo)
        self.wins += winner * undo
        self.losses += (not winner) * undo
        self.current_win_streak = self.current_win_streak + 1 if winner else 0
        self.current_lose_streak = self.current_lose_streak + 1 if not winner else 0
        self.nb_matches += 1 * undo
        self.double_xp -= (1 * undo) * (self.double_xp > 0)
        self.wlr = self.wins if self.losses == 0 else self.wins / self.losses
        if winner and self.current_win_streak > self.most_wins_in_a_row:
            self.most_wins_in_a_row += 1 * undo
        elif not winner and self.current_lose_streak > self.most_losses_in_a_row:
            self.most_losses_in_a_row += 1 * undo

    def __str__(self):
        """Print all attributes of the player."""
        res = '```\n'
        for stat in Player.STATS:
            if stat == "wlr":
                res += f'{stat:<25} {getattr(self, stat):>14.3f}\n'
            elif stat == "last_join":
                res += f'{stat:<25} {self.last_join.strftime("%d/%m/%Y"):>14}\n'
            elif stat == "fav_pos":
                res += f'{stat:<25} {" ".join(self.fav_pos):>14}\n'
            else:
                res += f'{stat:<25} {str(getattr(self, stat)):>14}\n'
        res += '```'
        return res


if __name__ == '__main__':
    p = Player("Anddy", 50)
    print(p.__dict__)
    print(p)
