import discord
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from thestarboard.bot import Bot
from thestarboard.translator import translate


class StarboardCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    config = app_commands.Group(
        # Command group name (/config)
        name=_("config"),
        # Command group description (/config)
        description=_("Starboard configuration."),
        default_permissions=discord.Permissions(manage_guild=True),
        guild_only=True,
    )

    @config.command(
        # Subcommand name (/config set-channel)
        name=_("set-channel"),
        # Subcommand description (/config set-channel)
        description=_("Sets the starboard channel to send messages to."),
    )
    @app_commands.rename(
        # Subcommand parameter name (/config set-channel [channel])
        channel=_("channel"),
    )
    @app_commands.describe(
        # Subcommand parameter description (/config set-channel [channel])
        channel=_("The channel to send starboard messages to."),
    )
    async def config_set_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None,
    ):
        assert interaction.guild is not None

        async with self.bot.query.acquire() as query:
            if channel is not None:
                assert channel.guild is not None
                assert channel.guild == interaction.guild

                channel_id = channel.id
                guild_id = channel.guild.id
            else:
                channel_id = None
                guild_id = interaction.guild.id

            original_channel_id = await query.get_starboard_channel(guild_id)
            channel_changed = channel_id != original_channel_id

            if channel_changed:
                await query.set_starboard_channel(channel_id, guild_id=guild_id)

            responses: dict[tuple[bool, bool], _] = {
                # Response from /config set-channel
                (True, True): _("Successfully set the starboard channel to {0}!"),
                # Response from /config set-channel
                (True, False): _("Successfully unset the starboard channel!"),
                # Response from /config set-channel
                (False, True): _("{0} is already the starboard channel!"),
                # Response from /config set-channel
                (False, False): _("There is already no starboard channel set!"),
            }

            channel_set = channel_id is not None
            response_key = responses[channel_changed, channel_set]
            content = await translate(response_key, interaction)
            if channel_set:
                content = content.format(f"<#{channel_id}>")
            await interaction.response.send_message(content, ephemeral=True)

    # TODO: /config set-threshold
