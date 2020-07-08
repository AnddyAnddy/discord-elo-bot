import random
import discord
from discord import Embed
from main import GAMES
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, CheckFailure, MissingRequiredArgument
import utils.decorators as decorators
from utils.decorators import check_category, is_arg_in_modes, check_channel
from utils.utils import is_url_image
from modules.rank import Rank


class Init(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_permissions(manage_roles=True)
    async def init_elo_by_anddy(self, ctx):
        """Init the bot in the server.

        Initialize the bot to be ready on a guild.
        This command creates every channel needed for the Bot to work.
        This also build two categories Elo by Anddy and Modes
        Can be used anywhere. Need to have manage_roles
        """
        guild = ctx.guild
        if not discord.utils.get(guild.roles, name="Elo Admin"):
            await guild.create_role(name="Elo Admin",
                                    permissions=discord.Permissions.all_channel(),
                                    color=0xAA0000)
            await ctx.send("Elo admin role created")

        if not discord.utils.get(guild.categories, name='Elo by Anddy'):
            perms_secret_chan = {
                guild.default_role:
                    discord.PermissionOverwrite(read_messages=False),
                guild.me:
                    discord.PermissionOverwrite(read_messages=True),
            }

            base_cat = await guild.create_category(name="Elo by Anddy")
            await guild.create_text_channel(name="Init",
                                            category=base_cat,
                                            overwrites=perms_secret_chan)
            await guild.create_text_channel(name="Moderators",
                                            category=base_cat,
                                            overwrites=perms_secret_chan)
            await guild.create_text_channel(name="Info_chat", category=base_cat)
            await guild.create_text_channel(name="Register", category=base_cat)
            await guild.create_text_channel(name="Submit", category=base_cat)
            await guild.create_text_channel(name="Game_announcement",
                                            category=base_cat)
            await guild.create_text_channel(name="Staff_application",
                                            category=base_cat)
            await guild.create_text_channel(name="Suggestions",
                                            category=base_cat)
            await guild.create_text_channel(name="Bans",
                                            category=base_cat)
            await guild.create_text_channel(name="bye",
                                            category=base_cat)
            await guild.create_text_channel(name="premium",
                                            category=base_cat)

            await guild.create_category(name="Modes")

            await guild.create_category(name="Teams")

            await ctx.send("Elo by Anddy created, init done, use !help !")

    @commands.command()
    @has_permissions(manage_roles=True)
    @check_channel('init')
    async def add_mode(self, ctx, mode):
        """Add a mode to the game modes.

        Example: !add_mode 4
        Will add the mode 4vs4 into the available modes, a channel will be
        created and the leaderboard will now have a 4 key.
        Can be used only in init channel by a manage_roles having user."""
        if mode.isdigit() and int(mode) > 0:
            nb_p = int(mode)
            if GAMES[ctx.guild.id].add_mode(nb_p):
                guild = ctx.message.guild
                solo_cat = discord.utils.get(guild.categories, name="Solo elo")
                teams_cat = discord.utils.get(guild.categories, name="Teams elo")
                await guild.create_text_channel(f'{nb_p}vs{nb_p}',
                                                category=solo_cat)
                await guild.create_text_channel(f'{nb_p}vs{nb_p}',
                                                category=teams_cat)
                await ctx.send(embed=Embed(color=0x00FF00,
                                           description="The game mode has been added."))
                if not discord.utils.get(guild.roles, name=f"{mode}vs{mode} Elo Player"):

                    await guild.create_role(name=f"{mode}vs{mode} Elo Player",
                        colour=discord.Colour(random.randint(0, 0xFFFFFF)))
                    await ctx.send(f"{mode}vs{mode} Elo Player role created")
                return

        await ctx.send(embed=Embed(color=0x000000,
                                   description="Couldn't add the game mode."))

    @commands.command()
    @has_permissions(manage_roles=True)
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    async def delete_mode(self, ctx, mode):
        GAMES[ctx.guild.id].remove_mode(int(mode))
        await ctx.send(embed=Embed(color=0x00FF00,
                                   description="The mode has been deleted, please delete the channel."))


    @commands.command()
    @has_permissions(manage_roles=True)
    @check_channel('init')
    @is_arg_in_modes(GAMES)
    # @args_at_pos_digits((0, 3, 4))
    # @rank_update(GAMES, (0, 3, 4))
    async def add_rank(self, ctx, mode, name, image_url, from_points, to_points):
        """Add a rank and set this rank to everyone having required points.

        mode is the N in NvsN.
        name is the name of the rank. Must be in " "
        from_points is the points required to have this rank.
        to_points is the max points of this rank.
        """
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        from_points = int(from_points)
        to_points = int(to_points)
        if to_points < from_points:
            await ctx.send("To points must be greater than from points")
            return
        if not is_url_image(image_url):
            await ctx.send("The url doesn't lead to an image. (png jpg jpeg)")
            return
        if name in game.ranks[mode]:
            await ctx.send("The rank couldn't be added, maybe it already exists.")
            return

        game.ranks[mode][name] = Rank(mode, name, image_url, from_points, to_points)
        await ctx.send("The rank was added and the players got updated.")

    @commands.command()
    @check_channel('init')
    async def setpickmode(self, ctx, mode, new_mode):
        """Set the pickmode to the new_mode set

        :param: new_mode must be a number [0, 1, 2, 3]:
            [random teams, balanced random, random cap, best cap]
        """
        game = GAMES[ctx.guild.id]
        mode = int(mode)
        new_mode = int(new_mode)
        if new_mode not in range(3):
            await ctx.send("Wrong new_mode given, read help pickmode")
            return
        pickmodes = ["random teams", "balanced random", "random cap", "best cap"]
        game.queues[mode].mode = new_mode
        game.queues[mode].pick_function = game.queues[mode].modes[new_mode]
        await ctx.send(f"Pickmode changed to {pickmodes[new_mode]}!")


    @commands.command()
    @check_channel('init')
    async def setfavpos(self, ctx, *args):
        """The arguments will now be in the list that players can pick as position.

        example:
        !setfavpos gk dm am st
        will allow the players to use
        !pos st gk am dm
        """
        game = GAMES[ctx.guild.id]
        setattr(game, "available_positions", list(args))
        await ctx.send(f"The available_positions are now {game.available_positions}")



    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, (MissingRequiredArgument, CheckFailure)):
    #         await ctx.send(embed=Embed(color=0x000000,
    #                                    description=f"{str(error)}\n"
    #                                    f"Read !help {ctx.invoked_with}"))
    #     else:
    #         print(ctx.invoked_with)
    #         raise error




def setup(bot):
    bot.add_cog(Init(bot))
