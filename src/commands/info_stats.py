from utils.decorators import check_category, is_arg_in_modes, check_channel
from discord import Embed
from discord.ext import commands
from main import GAMES
from utils.utils import get_player_lb_pos


class Info_stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['lb'])
    @is_arg_in_modes(GAMES)
    @check_category('Elo by Anddy')
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
        game = GAMES[ctx.guild.id]
        msg = await ctx.send(embed=game.leaderboard(int(mode), stat_key, 1))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")



    @commands.command(aliases=['stats'])
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def info(self, ctx, mode, name=""):
        """Show the info of a player.

        Example: !info 1 @Anddy
        With no argument, the !info will show the user's stats.
        With a player_name as argument, if the player exists, this will show
        is stats in the seized mode.
        Can be used only in info_chat channel.
        """
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        name = str(ctx.author.id) if not name else name[3: -1]
        if not name.isdigit():
            await ctx.send("You better ping the player !")
            return
        name = int(name)
        if name in game.leaderboards[mode]:
            player = game.leaderboards[mode][name]
            pos = get_player_lb_pos(game.leaderboards[mode], player, "elo")
            await ctx.send(embed=Embed(color=0x00FF00,
               description=str(player))\
               .set_thumbnail(url=game.get_rank_url(mode, player.elo, player))\
               .set_footer(text=f"Position on leaderboard: {pos}"))
        else:
            await ctx.send(embed=Embed(color=0x000000,
                                       description=f"No player called <@{name}>"))


    @commands.command(aliases=['match'])
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def info_match(self, ctx, mode, id_game):
        """Display the infos of a specific match."""
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        if not id_game.isdigit():
            raise commands.errors.MissingRequiredArgument
        id_game = int(id_game)
        req_game, game_not_from_archive = game.get_game(mode, id_game)
        if req_game is None:
            await ctx.send("I couldn't find the game... Maybe it doesn't exist.")
            return
        if not game_not_from_archive:
            queue, winner, elo = req_game
            color = 0xFF0000 if winner == 1 else 0x0000FF
            winner_str = "Red team" if winner == 1 else "Blue team"
            await ctx.send(embed=Embed(color=color,
                                       description=f"```"
                f"{'Id':12}: {id_game}\n"
                f"{'Winner':12}: {winner_str}\n"
                f"{'Red team':12}: {queue_elo.team_to_player_name(queue.red_team)}\n"
                f"{'Blue team':12}: {queue_elo.team_to_player_name(queue.blue_team)}\n"
                f"```"
            ))
        else:
            queue = req_game
            await ctx.send(embed=Embed(color=0x00FF00,
                                       description=f"```"
                f"{'Id':12}: {id_game}\n"
                f"{'Red team':12}: {queue_elo.team_to_player_name(queue.red_team)}\n"
                f"{'Blue team':12}: {queue_elo.team_to_player_name(queue.blue_team)}\n"
                f"```"
            ))


    @commands.command(aliases=['h'])
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def history(self, ctx, mode, name=""):
        """Show every matches the user played in.

        Example: !h 1 Anddy
        With no argument, the !info will show the user's stats.
        With a player_name as argument, if the player exists, this will show
        is stats in the seized mode.
        Can be used only in info_chat channel.
        """
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        name = str(ctx.author.id) if not name else name[3: -1]
        if not name.isdigit():
            await ctx.send("You better ping the player !")
            return
        name = int(name)

        if name in game.leaderboards[mode]:
            msg = await ctx.send(embed=game.history(mode,
                game.leaderboards[mode][name]))
            await msg.add_reaction("⏮️")
            await msg.add_reaction("⬅️")
            await msg.add_reaction("➡️")
            await msg.add_reaction("⏭️")
        else:
            await ctx.send(embed=Embed(color=0x000000,
               description=f"No player called <@{name}>"))



    @commands.command()
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    async def modes(self, ctx):
        """Print available modes."""
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=str(GAMES[ctx.guild.id].available_modes)))


    @commands.command(aliases=['bans'])
    @check_category('Elo by Anddy')
    @check_channel('bans')
    async def all_bans(self, ctx):
        GAMES[ctx.guild.id].remove_negative_bans()
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=GAMES[ctx.guild.id].all_bans()))



    @commands.command()
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def ranks(self, ctx, mode):
        """Show the available ranks."""
        msg = await ctx.send(embed=GAMES[ctx.guild.id].display_ranks(int(mode)))
        await msg.add_reaction("⏮️")
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("⏭️")


    @commands.command()
    @check_category('Elo by Anddy')
    @check_channel('info_chat')
    @is_arg_in_modes(GAMES)
    async def rank(self, ctx, mode, name):
        """Show the rank of the name."""
        ranks = GAMES[ctx.guild.id].ranks[int(mode)]
        if name not in ranks:
            await ctx.send(embed=Embed(color=0x000000),
                description="Couldn't find the rank with that name.")
            return

        await ctx.send(embed=Embed(color=0x00FF00,
            description=str(ranks[name])).set_thumbnail(url=ranks[name].url))

def setup(bot):
    bot.add_cog(Info_stats(bot))
