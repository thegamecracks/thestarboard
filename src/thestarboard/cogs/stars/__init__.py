from thestarboard.bot import Bot
from .events import StarboardEvents


async def setup(bot: Bot):
    await bot.add_cog(StarboardEvents(bot))
