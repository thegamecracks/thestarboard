# Concept

This document describes the primary features that the bot should implement.

## What is a Starboard?

A starboard records messages that have been starred by users.

## Usage

Users should be able to react with any star. Once a certain star has reached
the threshold, a starboard message is sent containing the star, the number
of reactions for that star. The message should also have an embed containing
the author icon, author name, original message content, and the first image/video
attachment if any.

## Configuration

A server admin should be able to:

- Set the starboard channel, or disable it
- Toggle automatic starboard message content edits
- Toggle automatic starboard message deletion
- Set the star threshold before sending/deleting a starboard message
- Set a maximum message age allowed to be sent to the starboard

Moderators should be able to remove starboard messages by clearing their reactions.

## Real-Time Updates

When a message is starred, un-starred, edited, or deleted,
the corresponding starboard message should be updated appropriately.

When a guild, channel, message, etc. is removed, the database should delete
those objects appropriately.

When no more stars exist for a message, it should be deleted from the database.

## Downtime And Synchronization

Starboard messages should NOT be refreshed upon a bot reconnect or restart.

No decision is made on whether an update should also make an API call
to refresh the number of reactions.

## Gateway Intents

The following intents are required:

- `guild_messages`

  Provides `on_raw_message_edit` / `on_raw_message_delete` events.

- `guild_reactions`

  Provides `on_raw_reaction_add` / `on_raw_reaction_remove` /
  `on_raw_reaction_clear` events.

- `guilds`

  Required for fundamental functionality of discord.py.

  Provides `on_guild_join` / `on_guild_remove` / `on_guild_channel_delete` events.

- `message_content`

  Provides content and attachments of messages.
