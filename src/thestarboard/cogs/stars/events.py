import discord
from discord.ext import commands

from thestarboard.bot import Bot


class StarboardEvents(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def _is_star_emoji(self, emoji: str) -> bool:
        return emoji in self.bot.config.starboard.allowed_emojis

    @commands.Cog.listener("on_raw_reaction_add")
    async def add_star_reaction(self, payload: discord.RawReactionActionEvent):
        """Adds a single message star."""
        if not self._is_star_emoji(payload.emoji.name):
            return

        async with self.bot.query.acquire() as query:
            await query.add_message_star(
                payload.message_id,
                payload.user_id,
                payload.emoji.name,
                channel_id=payload.channel_id,
                guild_id=payload.guild_id,
            )

        # Send/edit starboard message as necessary
        print("reaction added")

    @commands.Cog.listener("on_raw_reaction_remove")
    async def remove_star_reaction(self, payload: discord.RawReactionActionEvent):
        """Removes a single message star."""
        if not self._is_star_emoji(payload.emoji.name):
            return

        async with self.bot.query.acquire() as query:
            await query.remove_message_star(
                payload.message_id,
                payload.user_id,
                payload.emoji.name,
            )

        # Edit starboard message as necessary
        print("reaction removed")

    @commands.Cog.listener("on_raw_reaction_clear")
    async def clear_star_reactions(self, payload: discord.RawReactionClearEvent):
        """Removes all stars associated with the message."""
        # Delete all stars from message
        # Edit starboard message as necessary
        print("reactions cleared")

    @commands.Cog.listener("on_raw_reaction_clear_emoji")
    async def clear_one_star_reaction(
        self,
        payload: discord.RawReactionClearEmojiEvent,
    ):
        """Removes all stars of an emoji associated with the message."""
        if not self._is_star_emoji(payload.emoji.name):
            return

        # Delete all stars with emoji from message
        # Update starboard message as necessary
        print("reaction emoji cleared")

    @commands.Cog.listener("on_raw_message_delete")
    async def delete_starboard_message(self, payload: discord.RawMessageDeleteEvent):
        """Deletes the associated starboard message."""
        # Check if guild setting is enabled
        # Fetch starboard message
        # Delete starboard message
        print("message deleted")

    @commands.Cog.listener("on_raw_bulk_message_delete")
    async def bulk_delete_starboard_messages(self, payload: discord.RawBulkMessageDeleteEvent):
        """Bulk deletes the associated starboard messages."""
        # Check if guild setting is enabled
        # Fetch starboard messages
        # Delete starboard messages
        print("messages deleted")

    @commands.Cog.listener("on_raw_message_edit")
    async def edit_starboard_message(self, payload: discord.RawMessageUpdateEvent):
        """Updates the starboard message."""
        # Check if guild setting is enabled
        # Fetch starboard message
        # Edit starboard message
        print("message edited")
