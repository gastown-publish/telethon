"""Forum (topic) helpers for Telegram supergroups."""

from __future__ import annotations

import asyncio
import time

from telethon import TelegramClient
from telethon.tl import functions
from telethon.tl.types import ForumTopic, ForumTopicDeleted


async def get_topic_top_message_id(client: TelegramClient, entity, topic_id: int) -> int:
    """Resolve a forum ``topic_id`` to the **top message id** used for ``reply_to``."""
    peer = await client.get_input_entity(entity)
    res = await client(functions.messages.GetForumTopicsByIDRequest(peer=peer, topics=[topic_id]))
    if not res.topics:
        raise ValueError(f"No topic data returned for topic_id={topic_id}")
    t = res.topics[0]
    if isinstance(t, ForumTopicDeleted):
        raise ValueError(f"Topic {topic_id} is deleted")
    if isinstance(t, ForumTopic):
        return t.top_message
    raise ValueError(f"Topic {topic_id}: unexpected type {type(t).__name__}")


async def wait_for_bot_reply_in_thread(
    client: TelegramClient,
    group,
    bot_username: str,
    top_message_id: int,
    after_message_id: int,
    *,
    timeout: float = 45.0,
) -> str | None:
    """Wait for a new message from ``bot_username`` in the thread anchored at ``top_message_id``."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(group, limit=20, reply_to=top_message_id):
            if msg.id <= after_message_id:
                continue
            sender = await msg.get_sender()
            if sender and hasattr(sender, "username") and sender.username == bot_username:
                return msg.text or ""
    return None


async def send_in_topic(
    client: TelegramClient,
    group,
    text: str,
    top_message_id: int,
):
    """Send ``text`` into the forum thread (reply chain) anchored at ``top_message_id``."""
    return await client.send_message(group, text, reply_to=top_message_id)
