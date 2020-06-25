"""Elo."""


class Elo():
    """Docstring for elo."""

    def __init__(self):
        """Initialize at 0 every elo stats for a game."""
        self.red_average = 0
        self.blue_average = 0
        self.red_chance_to_win = 0
        self.blue_chance_to_win = 0
        self.red_rating = 0
        self.blue_rating = 0

    def update_team_averages(self, game_stats):
        """Load the new averages."""
        self.red_average = get_average_rank(game_stats.red_team)
        self.blue_average = get_average_rank(game_stats.blue_team)

    def update_chances_to_win(self):
        """Follow internet formula to calculate chances of winning of teams."""
        self.red_chance_to_win = 1 / \
            (1 + 10 ** ((self.blue_average - self.red_average) / 400))
        self.blue_chance_to_win = 1 / \
            (1 + 10 ** ((self.red_average - self.blue_average) / 400))

    def update_rating(self, rwin, bwin):
        """Internet formula calculating the ratings."""
        self.red_rating = int(32 * (rwin - self.red_chance_to_win))
        self.blue_rating = int(32 * (bwin - self.blue_chance_to_win))

    def handle_elo_calc(self, game_stats):
        """Update the data."""
        self.update_team_averages(game_stats)
        self.update_chances_to_win()

    def update_elo(self, game_stats):
        """Update the elo of every players."""
        winners = game_stats.red_score > game_stats.blue_score
        self.update_rating(winners, not winners)
        for i in range(len(game_stats.red_team)):
            game_stats.red_team[i].elo += self.red_rating
            game_stats.blue_team[i].elo += self.blue_rating


def get_average_rank(team):
    """
    Return the average rank of a given team.

    team must contain object having elo attribute.
    """
    return sum(p.elo for p in team) / len(team)
