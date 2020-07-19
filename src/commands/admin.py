"""Module used to represent every commands an admin is able to do."""

import discord
from utils.decorators import check_category, check_channel, is_arg_in_modes, has_role_or_above
from discord import Embed
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from GAMES import GAMES
from queue_elo import Queue
from utils.exceptions import get_player_by_mention
from utils.exceptions import get_id
from utils.exceptions import get_total_sec
from utils.exceptions import get_game
from utils.exceptions import PassException


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['fr'])
    @check_category('Solo elo')
    @has_role_or_above('Elo Admin')
    async def force_remove(self, ctx, mention):
        """Remove the player from the current queue."""
        mode = int(ctx.channel.name.split('vs')[0])
        player = await get_player_by_mention(ctx, mode, mention)
        game = get_game(ctx)
        queue = game.queues[mode]
        await ctx.send(queue.remove_player(player))

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_category('Elo by Anddy')
    @check_channel('register')
    async def force_quit(self, ctx, mention):
        """Delete the seized user from the registered players.

        Example: !force_quit @Anddy
        The command is the same than quit_elo except that the user has to make
        someone else quit the Elo.
        This can be used only in Bye channel.
        Can't be undone."""
        game = get_game(ctx)
        id = await get_id(ctx, mention)
        game.erase_player_from_queues(id)
        game.erase_player_from_leaderboards(id)

        await ctx.send(embed=Embed(color=0x00FF00,
            description=f'{mention} has been removed from the rankings'))


    @commands.command(aliases=['cq', 'c_queue'])
    @has_role_or_above('Elo Admin')
    @check_category('Solo elo')
    async def clear_queue(self, ctx):
        """Clear the current queue."""
        game = get_game(ctx)
        mode = int(ctx.channel.name.split('vs')[0])
        last_id = game.queues[mode].game_id
        if not game.queues[mode].has_queue_been_full:
            game.queues[mode] = Queue(
                2 * mode, game.queues[mode].mode,
                game.queues[mode].mapmode, last_id)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The queue is now empty"))



    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('bans')
    async def ban(self, ctx, mention, time, unity, *reason):
        """Bans the player for a certain time.

        unity must be in s, m, h, d (secs, mins, hours, days).
        reason must be into " "
        """

        id = await get_id(ctx, mention)
        total_sec = await get_total_sec(ctx, time, unity)
        get_game(ctx).ban_player(id, total_sec, ' '.join(reason))
        await ctx.send(embed=Embed(color=0x00FF00,
            description=f"{mention} has been banned ! Check !bans"))


    @commands.command()
    @check_channel('bans')
    @has_role_or_above('Elo Admin')
    async def unban(self, ctx, mention):
        """Unban the player."""
        id = await get_id(ctx, mention)
        get_game(ctx).unban_player(id)
        await ctx.send(embed=Embed(color=0x00FF00,
            description=f"{mention} has been unbanned ! Check !bans"))



    @commands.command()
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    async def setelo(self, ctx, mode, name, elo):
        """Set the elo to the player in the specific mode."""
        get_game(ctx).set_elo(int(mode), int(name[3: -1]), int(elo))
        await ctx.send("Worked!")

    @commands.command()
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    async def setallstats(self, ctx, mode, name, *stats):
        """Set the stats to the player in the specific mode.
        Let any stat to -1 to not let it change.
        In order:
            [elo, wins, losses, nb_matches, wlr, most_wins_in_a_row,
            most_losses_in_a_row, current_win_streak,
            current_lose_streak, double_xp]
            The wlr will anyway be calculated at the end.
        """
        player = get_game(ctx).leaderboards[int(mode)][int(name[3: -1])]
        stats_name = Player.STATS[1: -1]
        if len(stats) > len(stats_name):
            await ctx.send("Too much arguments ! I'll cancel in case you messed up")
            return

        for i, stat in enumerate(stats):
            try:
                stat = int(stat)
                if stat >= 0:
                    setattr(player, stats_name[i], stat)
            except ValueError:
                await ctx.send(f"Wrong format for {stats_name[i]}.")

        player.wlr = player.wins / player.losses if player.losses != 0 else 0
        await ctx.send("Worked!")

    @commands.command()
    @check_channel('init')
    async def setdoublexp(self, ctx, player, value):
        game = get_game(ctx)
        player = int(player[3: -1])
        for mode in game.available_modes:
            if player in game.leaderboards[mode]:
                game.leaderboards[mode][player].double_xp = int(value)

    @commands.command(aliases=['rmsp'])
    @check_channel('init')
    async def remove_non_server_players(self, ctx):
        """Remove people that aren't in the server anymore."""
        game = get_game(ctx)
        guild = self.bot.get_guild(ctx.guild.id)
        start = sum(len(v) for mode, v in game.leaderboards.items())
        for mode in game.available_modes:
            game.leaderboards[mode] = {
                id: player for id, player in game.leaderboards[mode].items()
                if guild.get_member(id) is not None
            }
        end = sum(len(v) for mode, v in game.leaderboards.items())

        await ctx.send(embed=Embed(color=0x00FF00,
            description=f"You kicked {start - end} members from the leaderboards"))

def setup(bot):
    bot.add_cog(Admin(bot))
