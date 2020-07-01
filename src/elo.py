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

    def update_elo(self, queue, winners):
        """Update the elo of every players.

        :param: queue must be a queue in undecided games
        :param: winners must be the id of the winning team [1, 2]
        """
        winners -= 1
        self.update_rating(winners, not winners)
        for i in range(len(queue.red_team)):
            queue.red_team[i].update(self.red_rating, not winners)
            queue.blue_team[i].update(self.blue_rating, winners)

    def undo_elo(self, queue, winners, rating):
        """Reversed operation of update_elo."""
        winners -= 1
        for i in range(len(queue.red_team)):
            queue.red_team[i].update(rating, not winners, -1)
            queue.blue_team[i].update(-1 * rating, winners, -1)

    def update(self, queue, winners):
        """Update the stats after a game for every player."""
        self.handle_elo_calc(queue)
        self.update_elo(queue, winners)


def get_average_rank(team):
    """
    Return the average rank of a given team.

    team must contain object having elo attribute.
    """
    return sum(p.elo for p in team) / len(team)
