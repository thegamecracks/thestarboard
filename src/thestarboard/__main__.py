import argparse
import functools
import importlib.metadata
import logging
import sys
from pathlib import Path

import discord

from .bot import Bot
from .config import load_config

parser = argparse.ArgumentParser(
    prog=__package__,
    description=importlib.metadata.metadata("thestarboard")["Summary"],
)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase logging verbosity",
)
parser.add_argument(
    "--config-file",
    default="config.toml",
    help="The config file to load",
    type=Path,
)

args = parser.parse_args()
config_file: Path = args.config_file

root_level = logging.INFO
if args.verbose > 0:
    log = logging.getLogger(__package__)
    log.setLevel(logging.DEBUG)
if args.verbose > 1:
    root_level = logging.DEBUG

# Configure logging early to capture our own initialization
discord.utils.setup_logging(
    level=root_level,
    root=True,
)

bot = Bot(functools.partial(load_config, config_file))

if bot.config.bot.token == "":
    sys.exit(
        "No bot token has been supplied by the config file.\n"
        "Please get a Bot Token from https://discord.com/developers/applications "
        "and add it to your configuration."
    )

bot.run(
    bot.config.bot.token,
    log_handler=None,
)
