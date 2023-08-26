from thestarboard.bot import Bot

from .commands import StarboardCommands
from .events import StarboardEvents


async def setup(bot: Bot):
    await bot.add_cog(StarboardCommands(bot))
    await bot.add_cog(StarboardEvents(bot))
