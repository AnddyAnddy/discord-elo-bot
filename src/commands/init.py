import random

import discord
from discord import Embed
from discord.ext import commands

from main import GAMES
from src.modules.game import Game
from src.modules.rank import Rank
from src.utils.decorators import is_arg_in_modes, check_channel, has_role_or_above
# from utils.exceptions import get_player_by_id, get_player_by_mention
from src.utils.exceptions import get_game
from src.utils.utils import create_mode_discord
from src.utils.utils import is_url_image
from src.utils.utils import split_with_numbers


class Init(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def init_elo_by_anddy(self, ctx):
        """Init the bot in the server.

        Initialize the bot to be ready on a guild.
        This command creates every channel needed for the Bot to work.
        Can be used anywhere. Need to have Elo Admin role
        Read https://github.com/AnddyAnddy/discord-elo-bot/wiki/How-to-set-up
        """
        guild = ctx.guild
        if not discord.utils.get(guild.roles, name="Elo Admin"):
            await guild.create_role(name="Elo Admin",
                                    # permissions=discord.Permissions.all_channel(),
                                    colour=discord.Colour(0xAA0000))
            await ctx.send("Elo admin role created. Since I don't know the "
                           "layout of your roles, I let you put this new role above "
                           "normal users.")

        if not discord.utils.get(guild.categories, name='Elo by Anddy'):
            perms_secret_channel = {
                guild.default_role:
                    discord.PermissionOverwrite(read_messages=False),
                guild.me:
                    discord.PermissionOverwrite(read_messages=True),
                discord.utils.get(guild.roles, name="Elo Admin"):
                    discord.PermissionOverwrite(read_messages=True)
            }

            base_cat = await guild.create_category(name="Elo by Anddy")
            await guild.create_text_channel(name="Init",
                                            category=base_cat,
                                            overwrites=perms_secret_channel)
            await guild.create_text_channel(name="Moderators",
                                            category=base_cat,
                                            overwrites=perms_secret_channel)
            await guild.create_text_channel(name="Info_chat", category=base_cat)
            await guild.create_text_channel(name="Register", category=base_cat)
            await guild.create_text_channel(name="Submit", category=base_cat)
            await guild.create_text_channel(name="Game_announcement",
                                            category=base_cat)
            await guild.create_text_channel(name="Bans",
                                            category=base_cat)
            await guild.create_text_channel(name="announcements",
                                            category=base_cat)
            await guild.create_category(name="Solo elo")

            await guild.create_category(name="Teams elo")

            await ctx.send("Elo by Anddy created, init done, use !help !")

        if ctx.guild.id not in GAMES:
            GAMES[guild.id] = Game(guild.id)

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('init')
    @commands.guild_only()
    async def add_mode(self, ctx, mode):
        """Add a mode to the game modes.

        Example: !add_mode 4s
        Will add the mode solo 4vs4 into the available modes, a channel will be
        created and the embed_leaderboard will now have a 4s key.
        Can be used only in init channel by a Elo Admin role having user."""
        split = split_with_numbers(mode)
        if len(split) == 2:
            num, vs_mode = split

            if num.isdigit() and int(num) > 0 and vs_mode in ("s", "t"):
                if get_game(ctx).add_mode(mode):
                    guild = ctx.message.guild
                    await create_mode_discord(num,
                                              {"s": "Solo elo", "t": "Teams elo"}[vs_mode], ctx)
                    if not discord.utils.get(guild.roles,
                                             name=f"{num}vs{num} Elo Player"):
                        await guild.create_role(name=f"{num}vs{num} Elo Player",
                                                colour=discord.Colour(random.randint(0, 0xFFFFFF)))
                        await ctx.send(f"{num}vs{num} Elo Player role created")
                    return

        await ctx.send(embed=Embed(color=0x000000,
                                   description="Couldn't add the game mode."))

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('init')
    @is_arg_in_modes()
    @commands.guild_only()
    async def delete_mode(self, ctx, mode):
        get_game(ctx).remove_mode(mode)
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The mode has been deleted, please delete the channel."))

    @staticmethod
    @commands.guild_only()
    async def add_rank_aux(ctx, mode, name, image_url, from_points, to_points):
        game = get_game(ctx)
        from_points = int(from_points)
        to_points = int(to_points)
        if to_points < from_points:
            await ctx.send("To points must be greater than from points")
            return False
        if not is_url_image(image_url):
            await ctx.send("The url doesn't lead to an image. (png jpg jpeg)")
            return False
        if name in game.ranks[mode]:
            await ctx.send("The rank couldn't be added, maybe it already exists.")
            return False
        game.ranks[mode][name] = Rank(mode, name, image_url, from_points, to_points)
        return True

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('init')
    @commands.guild_only()
    async def set_default_ranks(self, ctx):
        """Initialize the ranks to the defaults ones provided by Anddy.
        """
        game = get_game(ctx)
        elo_spread = [(0, 900)] + [(x, x + 50) for x in range(900, 1300, 50)] + [(1300, 9999)]
        names = [f"{name}{i}" for name in ("Platinum", "Diamond", "Master") for i in range(3, 0, -1)] + ["Legend"]
        with open("rank_links.txt") as f:
            images = ([elem[:-1] for elem in f.readlines()])

        for mode in game.get_leaderboards():
            for (from_p, to_p), name, image in zip(elo_spread, names, images):
                await self.add_rank_aux(ctx, mode, name, image, from_p, to_p)

        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="All the ranks were added ! check !ranks"))

    @commands.command()
    @has_role_or_above('Elo Admin')
    @check_channel('init')
    @is_arg_in_modes()
    # @args_at_pos_digits((0, 3, 4))
    # @rank_update(GAMES, (0, 3, 4))
    @commands.guild_only()
    async def add_rank(self, ctx, mode, name, image_url, from_points, to_points):
        """Add a rank and set this rank to everyone having required points.

        mode is the N in NvsN.
        name is the name of the rank. Must be in " "
        from_points is the points required to have this rank.
        to_points is the max points of this rank.
        """
        if self.add_rank_aux(ctx, mode, name, image_url, from_points, to_points):
            await ctx.send("The rank was added and the players got updated.")

    @commands.command()
    @check_channel('init')
    @is_arg_in_modes()
    @commands.guild_only()
    async def set_pick_mode(self, ctx, mode, new_mode):
        """Set the pick_mode to the new_mode set

        new mode:
            0: random teams
            1: balanced teams
            2: random cap, picks 1-1 1-1
            3: best cap, picks 1-1 1-1
            4: random cap, picks 1-2 2-1
            5: best cap, picks 1-2 2-1
        """
        game = get_game(ctx)
        new_mode = int(new_mode)
        if split_with_numbers(mode)[1] == 't':
            await ctx.send("Can't set a pick_mode for team vs team")
            return
        if new_mode not in range(6):
            await ctx.send("Wrong new_mode given, read help pick_mode")
            return
        pick_modes = ["random teams", "balanced random", "random cap (1-1)",
                      "best cap (1-1)", "random cap (1-2 2-1)", "best cap (1-2 2-1)"]
        game.queues[mode].mode = new_mode
        if len(game.queues[mode].modes) <= 4:  # backward compatibility
            game.queues[mode].modes.append(game.queues[mode].modes[2])
            game.queues[mode].modes.append(game.queues[mode].modes[3])
        game.queues[mode].pick_function = game.queues[mode].modes[new_mode]
        await ctx.send(f"Pick mode changed to {pick_modes[new_mode]} !")

    @commands.command()
    @check_channel('init')
    @commands.guild_only()
    async def set_fav_pos(self, ctx, *args):
        """The arguments will now be in the list that players can pick as position.

        example:
        !set_fav_pos gk dm am st
        will allow the players to use
        !pos st gk am dm
        """
        game = get_game(ctx)
        setattr(game, "available_positions", list(args))
        await ctx.send(f"The available_positions are now {game.available_positions}")

    @commands.command()
    @check_channel('init')
    @commands.guild_only()
    async def add_map(self, ctx, emoji, name):
        """Add the map in the available embed_maps."""
        await ctx.send(get_game(ctx).add_map(emoji, name))

    @commands.command()
    @check_channel('init')
    @commands.guild_only()
    async def delete_map(self, ctx, name):
        """Delete the map from the available embed_maps."""
        await ctx.send(get_game(ctx).delete_map(name))

    @commands.command()
    @check_channel('init')
    @is_arg_in_modes()
    @commands.guild_only()
    async def set_map_pick(self, ctx, mode, pick_mode):
        """Set the way to pick embed_maps.

        0: Maps aren't used
        1: The map is randomly picked
        2: The map is picked with emojis
        """
        if not pick_mode.isdigit() or int(pick_mode) not in range(3):
            await ctx.send(embed=Embed(color=0x000000,
                                       description="Incorrect pick_mode, read !help pick_mode."))
            return
        pick_mode = int(pick_mode)
        game = get_game(ctx)
        game.queues[mode].map_mode = pick_mode
        pick_modes = ["Maps aren't used", "The map is randomly picked",
                      "The map is picked with emojis"]
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description=f"The pick mode is set to: {pick_modes[pick_mode]}."))


def setup(bot):
    bot.add_cog(Init(bot))
