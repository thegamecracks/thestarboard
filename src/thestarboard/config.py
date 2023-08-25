from __future__ import annotations

import contextlib
import importlib.resources
import io
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal, Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    import asyncpg
    import discord

_package_files = importlib.resources.files(__package__)
CONFIG_DEFAULT_RESOURCE = _package_files.joinpath("config_default.toml")


class _BaseModel(BaseModel):
    class Config:
        extra = "forbid"


# https://docs.pydantic.dev/usage/settings/
class Settings(_BaseModel):
    bot: SettingsBot
    db: SettingsDB
    starboard: SettingsStarboard


class SettingsBot(_BaseModel):
    allow_jishaku: bool
    extensions: list[str]
    intents: SettingsBotIntents
    token: str


class SettingsBotIntents(_BaseModel):
    """The intents used when connecting to the Discord gateway.

    Default intents are enabled but can be overridden here.

    .. seealso:: https://discordpy.readthedocs.io/en/stable/api.html#intents

    """

    class Config:
        extra = "allow"

    def create_intents(self) -> discord.Intents:
        import discord

        intents = dict(discord.Intents.default())
        intents |= self.model_dump()
        return discord.Intents(**intents)


class SettingsDB(_BaseModel):
    dsn: str
    """The data source name used for connecting to the database.

    Should be in the format::

        postgres://user:password@host:port/database?option=value

    """
    password_file: str
    """An optional file to read the database password from."""

    @contextlib.asynccontextmanager
    async def create_pool(self) -> AsyncGenerator[asyncpg.Pool, None]:
        import asyncpg

        kwargs = {
            "dsn": self.dsn,
        }
        if self.password_file != "":
            kwargs["password"] = Path(self.password_file).read_text(encoding="utf-8")

        async with asyncpg.create_pool(**kwargs) as pool:
            yield pool


class SettingsStarboard(_BaseModel):
    allowed_emojis: list[str]
    """A list of emojis eligible for the starboard."""


Settings.model_rebuild()
SettingsBot.model_rebuild()


class OpenableBinary(Protocol):
    def open(self, __mode: Literal["rb"], /) -> io.BufferedIOBase:
        ...


def _recursive_update(dest: dict, src: dict) -> None:
    for k, vsrc in src.items():
        vdest = dest.get(k)
        if isinstance(vdest, dict) and isinstance(vsrc, dict):
            _recursive_update(vdest, vsrc)
        else:
            dest[k] = vsrc


def _load_raw_config(path: OpenableBinary) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def load_default_config() -> Settings:
    """Loads the default configuration file.

    :returns: The settings that were parsed.
    :raises FileNotFoundError:
        The default configuration file could not be found.

    """
    data = _load_raw_config(CONFIG_DEFAULT_RESOURCE)
    return Settings.model_validate(data)


def load_config(path: Path, *, merge_default: bool = True) -> Settings:
    """Loads the bot configuration file.

    :param merge_default:
        If True, the default configuration file will be used as a base
        and the normal configuration is applied on top of it,
        if it exists.
    :returns: The settings that were parsed.
    :raises FileNotFoundError:
        If merge_default is False, this means the configuration file
        could not be found. Otherwise, it means the default configuration
        file could not be found.

    """
    if not merge_default:
        data = _load_raw_config(path)
    elif path.exists():
        data = _load_raw_config(CONFIG_DEFAULT_RESOURCE)
        overwrites = _load_raw_config(path)
        _recursive_update(data, overwrites)
    else:
        data = _load_raw_config(CONFIG_DEFAULT_RESOURCE)

    return Settings.model_validate(data)
