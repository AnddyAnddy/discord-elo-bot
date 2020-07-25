"""Simulation of queue."""
from random import shuffle
from random import choice
from random import sample
from utils.exceptions import send_error
from utils.exceptions import PassException
from discord import Embed

class Queue():
    """Docstring for Queue."""
    def __init__(self, max_queue, mode, mapmode, last_id=0):
        """Initialize the queue."""
        if max_queue < 2 or max_queue % 2 == 1:
            raise ValueError("The max queue must be an even number > 2")
        self.players = []
        self.timeout = {}
        self.red_team = []
        self.blue_team = []
        self.max_queue = max_queue
        self.has_queue_been_full = False
        self.modes = [self.random_team, self.balanced_random,
            self.random_cap, self.best_cap, self.random_cap,
            self.best_cap, self.top_bottom]
        self.pick_fonction = self.modes[mode]
        self.mode = mode
        self.mapmode = mapmode
        self.game_id = last_id + 1

    def is_full(self):
        """Return true if the queue is full."""
        return self.max_queue == len(self.players)

    async def add_player(self, ctx, player, game):
        """Add a player in the queue."""
        if player in self.players:
            await send_error(ctx, "You can't join twice, maybe you're looking for !l")
            return
            # raise PassException()
        if self.is_full() or self.has_queue_been_full:
            await send_error(ctx, "Queue is full...")
            raise PassException()
        self.players.append(player)
        # self.timeout[player] = Timer(60 * 10, self.remove_player, (player, ))
        # self.timeout[player].start()
        res = f'<@{player.id_user}> has been added to the queue. '\
            f'**[{len(self.players)}/{int(self.max_queue)}]**'
        if self.is_full():
            res += "\nQueue is full, let's start the next session.\n"
            res += self.on_queue_full(game)
        return res

    async def add_players(self, ctx, players, game):
        """Add multiple players in the queue."""
        success = True
        len_at_start = len(self.players)
        for player in players:
            if player in self.players or self.is_full() or self.has_queue_been_full:
                success = False
                break
            self.players.append(player)
        if not success:
            len_at_end = len(self.players)
            for _ in range(len_at_end - len_at_start):
                self.players.pop()
            await send_error(ctx, "One or more of your players cannot be added,\n")
            raise PassException()
        await ctx.send(embed=Embed(color=0x00FF00, description=\
            f"Your team: {team_to_player_id(players)} was correctly added."))
        res = ""
        if self.is_full():
            res += "\nQueue is full, let's start the next session.\n"
            res += self.on_queue_full(game)
        return res

    def remove_player(self, player):
        """Remove a player from the queue."""
        if player in self.players and not self.has_queue_been_full:
            self.players.remove(player)
            return f'<@{player.id_user}> was removed from the queue\
                **[{len(self.players)} / {int(self.max_queue)}]**'
        return f"<@{player.id_user}> can't be removed from the queue"

    def on_queue_full(self, game):
        """Set a game."""
        self.has_queue_been_full = True
        # for t in self.timeout.values():
        #     t.cancel()
        self.timeout = {}
        self.pick_fonction()
        self.map_pick(game)
        return f'Game n°{self.game_id}:\n' + message_on_queue_full(self.players,
                                                                   self.red_team,
                                                                   self.blue_team,
                                                                   self.max_queue)

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

    def best_cap(self):
        """Get the 2 best players and make them captain."""
        self.players.sort(key=lambda p: p.elo)
        self.red_team.append(self.players.pop())
        self.blue_team.append(self.players.pop())

    def random_cap(self):
        """Get 2 random players and make them captain."""
        shuffle(self.players)
        self.red_team.append(self.players.pop())
        self.blue_team.append(self.players.pop())

    def top_bottom(self):
        """The [0, n / 2] top players go to red team, the others to blue."""
        for _ in range(len(self.players) // 2):
            self.blue_team.append(self.players.pop())

        for _ in range(len(self.players)):
            self.red_team.append(self.players.pop())


    def map_pick(self, game):
        """Do the process of picking a map."""
        if self.mapmode == 0 or not game.available_maps:
            return None
        if self.mapmode == 1:
            game.maps_archive[self.max_queue // 2][self.game_id] =\
                [choice(list(game.available_maps))]
        else:
            game.maps_archive[self.max_queue // 2][self.game_id] =\
                sample(list(game.available_maps),
                    min(3, len(game.available_maps)))


    async def get_captain_team(self, ctx, player):
        """Return 1 if red, 2 if blue, 0 if none."""
        red_cap, blue_cap = self.red_team[0], self.blue_team[0]
        for i, p in enumerate([red_cap, blue_cap], start=1):
            if p == player:
                return i
        await send_error(ctx, "You are not captain.")
        raise PassException()

    def get_team_by_id(self, id):
        return self.red_team if id == 1 else self.blue_team

    async def set_player_team(self, ctx, team_id, player):
        """Move the player from the players to the team."""
        team = self.red_team if team_id == 1 else self.blue_team
        try:
            team.append(self.players.pop(self.players.index(player)))
        except Exception as e:
            await send_error(ctx, f"Couldn't find <@{player.id_user}> here.")
            raise PassException()


    def ping_everyone(self):
        """Ping everyone present in the queue."""
        return ' '.join([f"<@{p.id_user}>" for p in self.red_team + self.blue_team + self.players])

    def player_in_winners(self, winner, player):
        """Return True if the player won that game."""
        return winner == 1 and player in self.red_team or\
        winner == 2 and player in self.blue_team

    def __str__(self):
        """ToString."""
        res = f"Game n°{self.game_id}\n"
        if not self.has_queue_been_full:
            return res + display_team(self.players, "Players", self.max_queue)
        return res + message_on_queue_full(self.players,
                                           self.red_team,
                                           self.blue_team,
                                           self.max_queue)


    def __contains__(self, elem):
        return elem in self.players or elem in self.red_team or elem in self.blue_team

def display_team(team, team_name, max_queue):
    """Show the player list of a specific team."""
    return f'```\n{team_name:20} {"Positions":20} {"Elo":>5}\n' + \
           '\n'.join([f"{i}) {p.name:20} {str(p.fav_pos_str()):20} {p.elo:>5}"
                      for i, p in enumerate(team, 1)]) + \
           f'```**[{len(team)}/{int(max_queue)}]**'


def message_on_queue_full(players, red_team, blue_team, max_queue):
    """Start the captain menu."""
    string = 'Two captains have been randomly picked !\n'
    string += f'<@{red_team[0].id_user}> is the red cap\n'
    string += f'<@{blue_team[0].id_user}> is the blue cap\n'

    string += display_team(red_team, "Red team", max_queue / 2)
    string += display_team(blue_team, "Blue team", max_queue / 2)
    string += display_team(players, "Remaining players", max_queue - 2)
    return string


def team_to_player_name(team):
    return "[" + ', '.join([f'{p.name}' for p in team]) + "]"


def team_to_player_id(team):
    return "[" + ', '.join([f'<@{p.id_user}>' for p in team]) + "]"


HISTORIQUE = []
if __name__ == '__main__':
    import doctest

    doctest.testfile("../test/queue.txt")
