from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING, Callable

import asyncpg
from discord.ext import commands

from .database import DatabaseClient
from .partials import PartialResolver
from .translator import GettextTranslator

if TYPE_CHECKING:
    from .config import Settings

log = logging.getLogger(__name__)


# https://discordpy.readthedocs.io/en/stable/ext/commands/api.html
class Bot(commands.Bot):
    pool: asyncpg.Pool
    query: DatabaseClient

    def __init__(self, config_refresher: Callable[[], Settings]):
        self._config_refresher = config_refresher
        config = self.refresh_config()

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=config.bot.intents.create_intents(),
            strip_after_prefix=True,
        )

        self.resolve = PartialResolver(self)

    async def _maybe_load_jishaku(self) -> None:
        if not self.config.bot.allow_jishaku:
            return

        try:
            version = importlib.metadata.version("jishaku")
        except importlib.metadata.PackageNotFoundError:
            pass
        else:
            await self.load_extension("jishaku")
            log.info("Loaded jishaku extension (version: %s)", version)

    def refresh_config(self) -> Settings:
        config = self._config_refresher()
        self.config = config
        return config

    async def setup_hook(self) -> None:
        for path in self.config.bot.extensions:
            await self.load_extension(path, package=__package__)
        log.info("Loaded %d extensions", len(self.config.bot.extensions))
        await self._maybe_load_jishaku()

        await self.tree.set_translator(GettextTranslator())

    async def start(self, *args, **kwargs) -> None:
        async with self.config.db.create_pool() as pool:
            self.pool = pool
            self.query = DatabaseClient(pool)
            return await super().start(*args, **kwargs)


class Context(commands.Context[Bot]):
    ...
