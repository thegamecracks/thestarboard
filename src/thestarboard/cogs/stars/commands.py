import datetime
from typing import cast

import discord
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from thestarboard.bot import Bot
from thestarboard.translator import plural_locale_str as ngettext, translate


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


class MaxMessageAgeTransformer(app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.integer

    @property
    def min_value(self) -> int:
        return 1

    @property
    def max_value(self) -> int:
        return 30

    async def autocomplete(
        self,
        interaction: discord.Interaction,
        value: int,
    ) -> list[app_commands.Choice[int]]:
        assert interaction.guild is not None

        bot = cast(Bot, interaction.client)
        async with bot.query.acquire() as query:
            max_age = await query.get_max_starboard_age(interaction.guild.id)

        # Response to user when seeing the maximum starboard message age
        message = await translate(
            ngettext(
                "Current max age: {0} day",
                "Current max age: {0} days",
            ),
            interaction,
            data=max_age.days,
        )
        message = message.format(max_age.days)

        return [app_commands.Choice(name=message, value=max_age.days)]

    async def transform(
        self,
        interaction: discord.Interaction,
        value: int,
    ) -> datetime.timedelta:
        return datetime.timedelta(days=value)


ThresholdTransform = app_commands.Transform[int, ThresholdTransformer]
MaxMessageAgeTransform = app_commands.Transform[
    datetime.timedelta,
    MaxMessageAgeTransformer,
]


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

    @config.command(
        # Subcommand name (/config set-max-age)
        name=_("set-max-age"),
        # Subcommand description (/config set-max-age)
        description=_("Sets the maximum age allowed for new starboard messages."),
    )
    @app_commands.rename(
        # Subcommand parameter name (/config set-max-age [max-age])
        max_age=_("max-age"),
    )
    @app_commands.describe(
        # Subcommand parameter description (/config set-max-age [max-age])
        max_age=_("The maximum age in days."),
    )
    async def config_set_max_age(
        self,
        interaction: discord.Interaction,
        max_age: MaxMessageAgeTransform,
    ):
        assert interaction.guild is not None
        guild_id = interaction.guild.id

        async with self.bot.query.acquire() as query:
            original_age = await query.get_max_starboard_age(guild_id)
            age_changed = max_age != original_age

            if age_changed:
                await query.set_max_starboard_age(max_age, guild_id=guild_id)

                # Response from /config set-max-age
                response_key = ngettext(
                    "Successfully set the maximum age to {0} day!",
                    "Successfully set the maximum age to {0} days!",
                )
            else:
                # Response from /config set-max-age
                response_key = ngettext(
                    "The current maximum age is {0} day!",
                    "The current maximum age is {0} days!",
                )

            content = await translate(response_key, interaction, data=max_age.days)
            content = content.format(max_age.days)
            await interaction.response.send_message(content, ephemeral=True)
