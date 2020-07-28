from utils.decorators import check_category, is_arg_in_modes, check_channel
from discord import Embed
from discord.ext import commands
from main import GAMES
from utils.utils import get_player_lb_pos, team_players_stats, most_stat_embed, build_most_played_with
from utils.exceptions import get_player_by_id, get_player_by_mention
from utils.exceptions import get_game
from utils.utils import add_scroll
from utils.utils import team_name
from modules.queue_elo import team_to_player_name


class Info_stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['lb'])
    @is_arg_in_modes(GAMES)
    @check_channel('info_chat')
    async def leaderboard(self, ctx, mode, stat_key="elo"):
        """Show current leaderboard.

        Example: !lb 1 wins
        Will show the leaderboard of the mode 1vs1 based on the wins.
        [mode] can be any mode in !modes.
        [stats key] can be any stat in !info. e.g:
        name, elo, wins, losses, nb_matches, wlr
        most_wins_in_a_row, most_losses_in_a_row.
        By default, if the stats key is missing, the bot will show the elo lb.
        """
        game = get_game(ctx)
        msg = await ctx.send(embed=game.leaderboard(mode, stat_key, 1))
        await add_scroll(msg)



    @commands.command(aliases=['stats'])
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def info(self, ctx, mode, mention=""):
        """Show the info of a player.

        Example: !info 1 @Anddy
        With no argument, the !info will show the user's stats.
        With a player_name as argument, if the player exists, this will show
        is stats in the seized mode.
        Can be used only in info_chat channel.
        """
        game = get_game(ctx)
        player = await get_player_by_mention(ctx, mode, mention) if mention\
            else await get_player_by_id(ctx, mode, ctx.author.id)

        pos = get_player_lb_pos(game.leaderboards[mode], player, "elo")
        await ctx.send(embed=Embed(color=0x00FF00,
            title=game.get_rank_name(mode, player.elo, player),
            description=str(player))\
            .set_thumbnail(url=game.get_rank_url(mode, player.elo, player))\
            .set_footer(text=f"Position on leaderboard: {pos}"))


    @commands.command(aliases=['match'])
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def info_match(self, ctx, mode, id_game):
        """Display the infos of a specific match."""
        game = get_game(ctx)
        if not id_game.isdigit():
            raise commands.errors.MissingRequiredArgument(id_game)
        id_game = int(id_game)
        req_game, game_not_from_archive = game.get_game(mode, id_game)
        if req_game is None:
            await ctx.send("I couldn't find the game... Maybe it doesn't exist.")
            return
        if not game_not_from_archive:
            queue, winner, elo = req_game
            color = 0xFF0000 if winner == 1 else 0x0000FF
            winner_str = team_name(winner)
            name, emoji = game.maps_archive[mode][id_game]\
                if id_game in game.maps_archive[mode] else ['map', 'no']
            await ctx.send(embed=Embed(color=color,
                                       description=f"```"
                f"{'Id':12}: {id_game}\n"
                f"{'Winner':12}: {winner_str}\n"
                f"{'Red team':12}: {team_to_player_name(queue.red_team)}\n"
                f"{'Blue team':12}: {team_to_player_name(queue.blue_team)}\n"
                f"{'Elo':12}: {elo} points\n"
                f"{'Map':12}: {emoji} {name}"
                f"```"
            ))
        else:
            queue = req_game
            maps = game.maps_archive[mode][id_game]\
                if id_game in game.maps_archive[mode] else 'no map'
            if (isinstance(maps, tuple)):
                maps = [maps]
            str_maps = ', '.join([f'{emoji}{name}' for name, emoji in maps])
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"```"
                f"{'Id':10}: {id_game}\n"
                f"{'Red team':10}: {team_to_player_name(queue.red_team)}\n"
                f"{'Blue team':10}: {team_to_player_name(queue.blue_team)}\n"
                f"{'Map':10}: {str_maps}"
                f"```"
            ))


    @commands.command(aliases=['h'])
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def history(self, ctx, mode, mention=""):
        """Show every matches the user played in.

        Example: !h 1 @Anddy
        With no argument, the !info will show the user's stats.
        With a player_name as argument, if the player exists, this will show
        is stats in the seized mode.
        Can be used only in info_chat channel.
        """
        game = get_game(ctx)
        player = await get_player_by_mention(ctx, mode, mention) if mention\
            else await get_player_by_id(ctx, mode, ctx.author.id)

        msg = await ctx.send(embed=game.history(mode, player))
        await add_scroll(msg)


    @commands.command()
    async def modes(self, ctx):
        """Print available modes."""
        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(get_game(ctx).available_modes)))


    @commands.command(aliases=['bans'])
    @check_channel('bans')
    async def all_bans(self, ctx):
        """Display all bans."""
        get_game(ctx).remove_negative_bans()
        await ctx.send(embed=Embed(color=0x00FF00,
            description=get_game(ctx).all_bans()))



    @commands.command()
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def ranks(self, ctx, mode):
        """Show the available ranks."""
        msg = await ctx.send(embed=get_game(ctx).display_ranks(mode))
        await add_scroll(msg)


    @commands.command()
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def rank(self, ctx, mode, name):
        """Show the rank of the name."""
        ranks = get_game(ctx).ranks[mode]
        if name not in ranks:
            await ctx.send(embed=Embed(color=0x000000,
                description="Couldn't find the rank with that name."))
            return

        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(ranks[name])).set_thumbnail(url=ranks[name].url))



    @commands.command()
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def most(self, ctx, mode, mention="", order_key="games", with_or_vs="with"):
        """Show who you played the most with.

        Example: !most losses @Anddy with
        Will show the leaderboard of the people with who you lost the most.
        order_key must € [games, draws, wins, losses]
        is the key the table will be ordered by."""
        game = get_game(ctx)

        player = await get_player_by_mention(ctx, mode, mention) if mention\
            else await get_player_by_id(ctx, mode, ctx.author.id)

        if order_key not in ("games", "draws", "wins", "losses"):
            raise commands.errors.BadArgument(order_key)
        if with_or_vs not in ("with", "vs"):
            raise commands.errors.BadArgument(with_or_vs)

        # most_played_with = build_most_played_with(game, mode, name)
        msg = await ctx.send(embed=most_stat_embed(game, mode, player,
            order_key, with_or_vs=with_or_vs))
        await add_scroll(msg)

    @commands.command()
    async def maps(self, ctx):
        """Show the available maps."""
        msg = await ctx.send(embed=get_game(ctx).maps())
        await add_scroll(msg)



def setup(bot):
    bot.add_cog(Info_stats(bot))
