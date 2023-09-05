from __future__ import annotations

import contextlib
import datetime
from contextvars import ContextVar
from typing import TYPE_CHECKING, AsyncGenerator, Self

from .cache import CacheSet, ExpiringMemoryCacheSet

if TYPE_CHECKING:
    import asyncpg

_current_conn: ContextVar[asyncpg.Connection] = ContextVar("_current_conn")


class DatabaseClient:
    """Provides an API for making common queries with an :class:`asyncpg.Pool`."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        *,
        cache: CacheSet | None = None,
    ) -> None:
        self.pool = pool
        self.cache: CacheSet = cache or ExpiringMemoryCacheSet(expires_after=1800)

    # Connection methods

    @property
    def conn(self) -> asyncpg.Connection:
        """Returns the current connection used by the query client.

        This is set by the :meth:`acquire()` method on a per-context basis.

        """
        try:
            return _current_conn.get()
        except LookupError:
            raise RuntimeError(
                "acquire() async context manager must be entered before "
                "running SQL statements"
            ) from None

    @contextlib.asynccontextmanager
    async def acquire(self, *, transaction: bool = True) -> AsyncGenerator[Self, None]:
        """Acquires a connection from the pool to be used by the client.

        :param transaction: If True, a transaction is opened as well.

        """
        async with self.pool.acquire() as conn:
            if transaction:
                transaction_manager = conn.transaction()
            else:
                transaction_manager = contextlib.nullcontext()

            async with transaction_manager:
                token = _current_conn.set(conn)
                try:
                    yield self
                finally:
                    _current_conn.reset(token)

    # Guild methods

    async def add_guild(self, guild_id: int) -> None:
        """Inserts the given guild ID into the database.

        If the guild exists, this is a no-op.

        """
        if not await self._try_cache_add("guild", guild_id):
            return

        await self.conn.execute(
            "INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING",
            guild_id,
        )

    # Channel methods

    async def add_channel(
        self,
        channel_id: int,
        *,
        guild_id: int | None = None,
    ) -> None:
        """Inserts the given channel ID into the database.

        If the channel exists, this is a no-op.
        Missing guilds are automatically inserted.

        """
        if not await self._try_cache_add("channel", f"{channel_id}-{guild_id}"):
            return

        if guild_id is not None:
            await self.add_guild(guild_id)

        await self.conn.execute(
            "INSERT INTO channel (id, guild_id) VALUES ($1, $2) "
            "ON CONFLICT (id) DO UPDATE SET\n"
            "    guild_id = COALESCE(excluded.guild_id, channel.guild_id)",
            channel_id,
            guild_id,
        )

    # User methods

    async def add_user(self, user_id: int) -> None:
        """Inserts the given user ID into the database.

        If the user exists, this is a no-op.

        """
        if not await self._try_cache_add("user", user_id):
            return

        await self.conn.execute(
            'INSERT INTO "user" (id) VALUES ($1) ON CONFLICT DO NOTHING',
            user_id,
        )

    # Message methods

    async def add_message(
        self,
        message_id: int,
        channel_id: int,
        user_id: int,
        *,
        guild_id: int | None = None,
    ):
        """Inserts the given message ID into the database.

        If the message exists, this is a no-op.
        Missing channels are automatically inserted.
        Missing guilds are automatically inserted.
        Missing users are automatically inserted.

        """
        if not await self._try_cache_add(
            "message",
            f"{message_id}-{channel_id}-{user_id}",
        ):
            return

        await self.add_channel(channel_id, guild_id=guild_id)
        await self.add_user(user_id)
        await self.conn.execute(
            "INSERT INTO message (id, channel_id, user_id) VALUES ($1, $2, $3) "
            "ON CONFLICT (id) DO UPDATE SET\n"
            "    channel_id = excluded.channel_id,\n"
            "    user_id = excluded.user_id",
            message_id,
            channel_id,
            user_id,
        )

    # Message star methods

    async def add_message_star(
        self,
        message_id: int,
        user_id: int,
        emoji: str,
        *,
        channel_id: int,
        guild_id: int | None = None,
    ):
        """Inserts the given message ID into the database.

        If the message exists, this is a no-op.
        Missing channels are automatically inserted.
        Missing guilds are automatically inserted.
        Missing users are automatically inserted.

        """
        # This method does not frequently collide, so no cache check needed
        await self.add_message(message_id, channel_id, user_id, guild_id=guild_id)
        await self.conn.execute(
            "INSERT INTO message_star (message_id, user_id, emoji) "
            "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            message_id,
            user_id,
            emoji,
        )

    async def remove_message_star(
        self,
        message_id: int,
        user_id: int,
        emoji: str,
    ) -> None:
        """Removes the given message star from the database.

        If the message star does not exist, this is a no-op.

        """
        # This method does not frequently collide, so no cache check needed
        await self.conn.execute(
            "DELETE FROM message_star "
            "WHERE message_id = $1 AND user_id = $2 AND emoji = $3",
            message_id,
            user_id,
            emoji,
        )

    async def get_message_star_total(self, message_id: int) -> int:
        """Gets a message's star total."""
        total = await self.conn.fetchval(
            "SELECT total FROM message_star_total WHERE message_id = $1",
            message_id,
        )
        return total or 0

    # Starboard message methods

    async def add_starboard_message(
        self,
        message_id: int,
        star_message_id: int,
    ):
        """Inserts the given starboard message into the database.

        Both message IDs must exist in the database beforehand.

        """
        await self.conn.execute(
            "INSERT INTO starboard_message (message_id, star_message_id) "
            "VALUES ($1, $2)",
            message_id,
            star_message_id,
        )

    async def get_starboard_message(self, message_id: int) -> int | None:
        """Gets the starboard message associated with the given message ID."""
        return await self.conn.fetchval(
            "SELECT message_id FROM starboard_message WHERE star_message_id = $1",
            message_id,
        )

    # Starboard configuration methods

    async def get_starboard_channel(self, guild_id: int) -> int | None:
        """Gets a guild's starboard channel.

        Missing guilds are automatically inserted.

        """
        await self.add_guild(guild_id)
        return await self.conn.fetchval(
            "SELECT starboard_channel_id FROM starboard_guild_config "
            "WHERE guild_id = $1",
            guild_id,
        )

    async def set_starboard_channel(
        self,
        channel_id: int | None,
        *,
        guild_id: int,
    ) -> None:
        """Sets a guild's starboard channel.

        Missing channels are automatically inserted.
        Missing guilds are automatically inserted.

        """
        if channel_id is not None:
            await self.add_channel(channel_id, guild_id=guild_id)

        await self.conn.execute(
            "UPDATE starboard_guild_config SET starboard_channel_id = $1 "
            "WHERE guild_id = $2",
            channel_id,
            guild_id,
        )

    async def get_starboard_threshold(self, guild_id: int) -> int:
        """Gets a guild's starboard threshold.

        Missing guilds are automatically inserted.

        """
        await self.add_guild(guild_id)
        threshold = await self.conn.fetchval(
            "SELECT star_threshold FROM starboard_guild_config "
            "WHERE guild_id = $1",
            guild_id,
        )
        # starboard_guild_config_trigger should guarantee this
        assert threshold is not None
        return threshold

    async def set_starboard_threshold(
        self,
        threshold: int,
        *,
        guild_id: int,
    ) -> None:
        """Sets a guild's starboard threshold.

        Missing guilds are automatically inserted.

        """
        await self.add_guild(guild_id)
        await self.conn.execute(
            "UPDATE starboard_guild_config SET star_threshold = $1 "
            "WHERE guild_id = $2",
            threshold,
            guild_id,
        )

    async def get_max_starboard_age(self, guild_id: int) -> datetime.timedelta:
        """Gets a guild's maximum starboard message age.

        Missing guilds are automatically inserted.

        """
        await self.add_guild(guild_id)
        max_message_age = await self.conn.fetchval(
            "SELECT max_message_age FROM starboard_guild_config "
            "WHERE guild_id = $1",
            guild_id,
        )
        # starboard_guild_config_trigger should guarantee this
        assert max_message_age is not None
        return datetime.timedelta(seconds=max_message_age)

    async def set_max_starboard_age(
        self,
        max_message_age: datetime.timedelta,
        *,
        guild_id: int,
    ) -> None:
        """Sets a guild's maximum starboard message age.

        `max_message_age` will rounded down to the second.

        Missing guilds are automatically inserted.

        """
        await self.add_guild(guild_id)
        await self.conn.execute(
            "UPDATE starboard_guild_config SET max_message_age = $1 "
            "WHERE guild_id = $2",
            int(max_message_age.total_seconds()),
            guild_id,
        )

    # Internal methods

    def _cache_key(self, bucket: str, id_: str | int) -> str:
        return f"{bucket}-{id_}"

    async def _try_cache_add(self, bucket: str, id_: str | int) -> bool:
        key = self._cache_key(bucket, id_)
        if await self.cache.exists(key):
            return False

        await self.cache.add(key)
        return True
