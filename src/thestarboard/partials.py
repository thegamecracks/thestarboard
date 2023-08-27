from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg
    import discord

    from .bot import Bot


class PartialResolver:
    """Provides methods for resolving partial objects from the database.

    All methods here require the :attr:`Bot.query` client to have a connection
    acquired beforehand.

    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @property
    def conn(self) -> asyncpg.Connection:
        """A shorthand for ``self.bot.query.conn``."""
        return self.bot.query.conn

    async def partial_message(
        self,
        message_id: int,
    ) -> discord.PartialMessage | None:
        """Attempts to resolve a partial message by ID."""
        row = await self.conn.fetchrow(
            "SELECT m.channel_id, c.guild_id FROM message m "
            "JOIN channel c ON m.channel_id = c.channel_id "
            "WHERE m.id = $1",
            message_id,
        )

        if row is None:
            return

        channel = self.bot.get_partial_messageable(
            row["channel_id"],
            guild_id=row["guild_id"],
        )
        return channel.get_partial_message(message_id)