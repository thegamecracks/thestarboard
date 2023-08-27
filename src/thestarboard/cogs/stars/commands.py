from typing import cast

import discord
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from thestarboard.bot import Bot
from thestarboard.translator import translate


class ThresholdTransformer(app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.integer

    @property
    def min_value(self) -> int:
        return 1

    @property
    def max_value(self) -> int:
        return 100

    async def autocomplete(
        self,
        interaction: discord.Interaction,
        value: int,
    ) -> list[app_commands.Choice[int]]:
        assert interaction.guild is not None

        bot = cast(Bot, interaction.client)
        async with bot.query.acquire() as query:
            threshold = await query.get_starboard_threshold(interaction.guild.id)

        # Response to user when seeing the star threshold
        message = await translate(_("Current star threshold: {0}"), interaction)
        message = message.format(threshold)

        return [app_commands.Choice(name=message, value=threshold)]

    async def transform(self, interaction: discord.Interaction, value: int) -> int:
        return value


ThresholdTransform = app_commands.Transform[int, ThresholdTransformer]


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

    @config.command(
        # Subcommand name (/config set-threshold)
        name=_("set-threshold"),
        # Subcommand description (/config set-threshold)
        description=_("Sets the number of stars required for a message to be pinned."),
    )
    @app_commands.rename(
        # Subcommand parameter name (/config set-threshold [threshold])
        threshold=_("threshold"),
    )
    @app_commands.describe(
        # Subcommand parameter description (/config set-threshold [threshold])
        threshold=_("The number of stars required."),
    )
    async def config_set_threshold(
        self,
        interaction: discord.Interaction,
        threshold: ThresholdTransform,
    ):
        assert interaction.guild is not None
        guild_id = interaction.guild.id

        async with self.bot.query.acquire() as query:
            original_threshold = await query.get_starboard_threshold(guild_id)
            threshold_changed = threshold != original_threshold

            if threshold_changed:
                await query.set_starboard_threshold(threshold, guild_id=guild_id)

                # Response from /config set-threshold
                response_key = _("Successfully set the star threshold to {0}!")
            else:
                # Response from /config set-threshold
                response_key = _("The current star threshold is {0}!")

            content = await translate(response_key, interaction)
            content = content.format(threshold)
            await interaction.response.send_message(content, ephemeral=True)
