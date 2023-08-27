from typing import Iterable

import discord
from discord.ext import commands

from thestarboard.bot import Bot


class StarboardEvents(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener("on_raw_reaction_add")
    async def add_star_reaction(self, payload: discord.RawReactionActionEvent):
        """Adds a single message star."""
        if payload.guild_id is None:
            return
        if not self._is_star_emoji(payload.emoji):
            return

        async with self.bot.query.acquire() as query:
            await query.add_message_star(
                payload.message_id,
                payload.user_id,
                str(payload.emoji),
                channel_id=payload.channel_id,
                guild_id=payload.guild_id,
            )

            await self._on_message_star_update(
                payload.message_id,
                guild_id=payload.guild_id,
            )

    @commands.Cog.listener("on_raw_reaction_remove")
    async def remove_star_reaction(self, payload: discord.RawReactionActionEvent):
        """Removes a single message star."""
        if payload.guild_id is None:
            return
        if not self._is_star_emoji(payload.emoji):
            return

        async with self.bot.query.acquire() as query:
            await query.remove_message_star(
                payload.message_id,
                payload.user_id,
                str(payload.emoji),
            )

            await self._on_message_star_update(
                payload.message_id,
                guild_id=payload.guild_id,
            )

    @commands.Cog.listener("on_raw_reaction_clear")
    async def clear_star_reactions(self, payload: discord.RawReactionClearEvent):
        """Removes all stars associated with the message."""
        if payload.guild_id is None:
            return

        async with self.bot.query.acquire() as query:
            await query.conn.execute(
                "DELETE FROM message_star WHERE message_id = $1",
                payload.message_id,
            )

            await self._on_message_star_update(
                payload.message_id,
                guild_id=payload.guild_id,
            )

    @commands.Cog.listener("on_raw_reaction_clear_emoji")
    async def clear_one_star_reaction(
        self,
        payload: discord.RawReactionClearEmojiEvent,
    ):
        """Removes all stars of an emoji associated with the message."""
        if payload.guild_id is None:
            return
        if not self._is_star_emoji(payload.emoji):
            return

        async with self.bot.query.acquire() as query:
            await query.conn.execute(
                "DELETE FROM message_star WHERE message_id = $1 AND emoji = $2",
                payload.message_id,
                str(payload.emoji),
            )

            await self._on_message_star_update(
                payload.message_id,
                guild_id=payload.guild_id,
            )

    @commands.Cog.listener("on_raw_message_delete")
    async def delete_starboard_message(self, payload: discord.RawMessageDeleteEvent):
        """Deletes the associated starboard message."""
        if payload.guild_id is None:
            return

        await self._delete_starboard_messages(
            (payload.message_id,),
            guild_id=payload.guild_id,
        )

    @commands.Cog.listener("on_raw_bulk_message_delete")
    async def bulk_delete_starboard_messages(
        self,
        payload: discord.RawBulkMessageDeleteEvent,
    ):
        """Bulk deletes the associated starboard messages."""
        if payload.guild_id is None:
            return

        await self._delete_starboard_messages(
            payload.message_ids,
            guild_id=payload.guild_id,
        )

    @commands.Cog.listener("on_raw_message_edit")
    async def edit_starboard_message(self, payload: discord.RawMessageUpdateEvent):
        """Updates the starboard message."""
        if payload.guild_id is None:
            return

        async with self.bot.query.acquire():
            await self._on_star_message_edit(
                payload.message_id,
                guild_id=payload.guild_id,
            )

    def _is_star_emoji(self, emoji: discord.PartialEmoji) -> bool:
        return str(emoji) in self.bot.config.starboard.allowed_emojis

    # Starboard content formatting

    def _format_star_counts(self, star_counts: dict[str, int]) -> str:
        """Formats a dictionary of star counts into a string summary."""
        return "  ".join(f"{star} **{count}**" for star, count in star_counts.items())

    async def _get_star_counts(self, message_id: int) -> dict[str, int]:
        """Gets star counts for a message through the database."""
        # TODO: occasionally synchronize star counts from Discord API
        star_counts: dict[str, int] = {}
        query = (
            "SELECT emoji, COUNT(*) AS count FROM message_star "
            "WHERE message_id = $1 "
            "GROUP BY emoji"
        )
        async for row in self.bot.query.conn.cursor(query, message_id):
            star_counts[row["emoji"]] = row["count"]
        return star_counts

    def _create_starboard_content(
        self,
        *,
        star_counts: dict[str, int],
        jump_url: str,
    ) -> str:
        """Creates a string to be used as the content of a starboard message."""
        stars = self._format_star_counts(star_counts)
        return f"{stars}  {jump_url}"

    # Starboard embed formatting

    def _get_image_url(self, message: discord.Message) -> str | None:
        """Gets a suitable URL to use for the starboard image."""
        for attachment in message.attachments:
            if attachment.content_type == "image":
                return attachment.url

        for embed in message.embeds:
            if embed.image.url is not None:
                return embed.image.url

    def _create_starboard_embed(self, message: discord.Message) -> discord.Embed:
        """Creates a starboard embed from the given message."""
        embed = discord.Embed(
            colour=0xFAF317,
            description=message.content,
            timestamp=message.created_at,
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar,
        )

        self._update_starboard_embed(
            embed,
            content=message.content,
            image_url=self._get_image_url(message),
        )

        return embed

    def _update_starboard_embed(
        self,
        embed: discord.Embed,
        *,
        content: str | None = None,
        image_url: str | None = None,
    ) -> discord.Embed:
        """Updates a starboard embed in-place with the given arguments."""
        if content is not None:
            embed.description = content
        if image_url is not None:
            embed.set_image(url=image_url)
        return embed

    # Starboard message creation

    async def _on_message_star_update(
        self,
        message_id: int,
        *,
        guild_id: int,
    ) -> None:
        """
        Sends, edits, or deletes the associated starboard message.

        The database client should have a connection acquired beforehand.
        Additionally, the `message_id` and `guild_id` parameters must already
        exist in the database.

        """
        query = self.bot.query

        starboard_message_id = await query.get_starboard_message(message_id)
        total = await query.get_message_star_total(message_id)
        threshold = await query.get_starboard_threshold(guild_id)

        if starboard_message_id is None and total >= threshold:
            # Decide if we should send a starboard message
            starboard_channel_id = await query.get_starboard_channel(guild_id)
            if starboard_channel_id is None:
                return

            starboard_channel = self.bot.get_partial_messageable(starboard_channel_id)

            message = await self.bot.resolve.message(message_id)
            assert message is not None

            content = self._create_starboard_content(
                star_counts=await self._get_star_counts(message_id),
                jump_url=message.jump_url,
            )
            embed = self._create_starboard_embed(message)

            try:
                starboard_message = await starboard_channel.send(content, embed=embed)
            except discord.Forbidden:
                await query.set_starboard_channel(None, guild_id=guild_id)
            else:
                await query.add_message(
                    starboard_message.id,
                    starboard_message.channel.id,
                    starboard_message.author.id,
                    guild_id=getattr(starboard_message.guild, "id", None),
                )
                await query.add_starboard_message(starboard_message.id, message_id)
        elif starboard_message_id is not None and total >= threshold:
            # Update star counts on existing message
            starboard_message = await self.bot.resolve.partial_message(
                starboard_message_id
            )
            assert starboard_message is not None

            message = await self.bot.resolve.partial_message(message_id)
            assert message is not None

            content = self._create_starboard_content(
                star_counts=await self._get_star_counts(message_id),
                jump_url=message.jump_url,
            )

            await starboard_message.edit(content=content)
        elif starboard_message_id is not None and total < threshold:
            # TODO: add guild setting to disable auto-deletion
            starboard_message = await self.bot.resolve.partial_message(
                starboard_message_id
            )
            assert starboard_message is not None

            await starboard_message.delete()

    async def _on_star_message_edit(
        self,
        message_id: int,
        *,
        guild_id: int,
    ):
        """
        Updates the associated starboard message's embedded content.

        The database client should have a connection acquired beforehand.
        Additionally, the `message_id` and `guild_id` parameters must already
        exist in the database.

        """
        query = self.bot.query

        # TODO: add guild setting to disable auto-edit

        starboard_message_id = await query.get_starboard_message(message_id)
        if starboard_message_id is None:
            return

        starboard_message = await self.bot.resolve.partial_message(starboard_message_id)
        assert starboard_message is not None
        message = await self.bot.resolve.message(message_id)
        assert message is not None

        embed = self._create_starboard_embed(message)

        await starboard_message.edit(embed=embed)

    async def _delete_starboard_messages(
        self,
        message_ids: Iterable[int],
        *,
        guild_id: int,
    ) -> None:
        """
        Attempts to delete the given starboard messages by ID
        if enabled in guild settings.

        The `guild_id` parameter must already exist in the database.

        """
        # TODO: add guild setting to disable auto-deletion

        # Filter message IDs for ones associated with a starboard message
        async with self.bot.pool.acquire() as conn, conn.transaction():
            query = (
                "SELECT sm.message_id, m.channel_id FROM starboard_message sm "
                "JOIN message m ON sm.message_id = m.id "
                "WHERE star_message_id = any($1::bigint[])"
            )
            starboard_messages: list[discord.PartialMessage] = []
            async for row in conn.cursor(query, message_ids):
                channel = self.bot.get_partial_messageable(row["m.channel_id"])
                message = channel.get_partial_message(row["sm.message_id"])
                starboard_messages.append(message)

        for m in starboard_messages:
            await m.delete(delay=0)
