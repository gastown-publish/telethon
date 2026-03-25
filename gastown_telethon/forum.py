"""Forum (topic) helpers for Telegram supergroups."""

from __future__ import annotations

import asyncio
import time

from telethon import TelegramClient
from telethon.tl import functions
from telethon.tl.types import ForumTopic, ForumTopicDeleted, MessageReplyHeader


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


async def wait_for_bot_reply_to_ping(
    client: TelegramClient,
    group,
    bot_username: str,
    ping_message_id: int,
    *,
    topic_id: int | None = None,
    top_message_id: int | None = None,
    timeout: float = 90.0,
) -> str | None:
    """Wait for a reply from ``bot_username`` after our ping (forum-safe).

    We cannot use ``iter_messages(..., reply_to=top_msg)`` on forums — Telegram returns
    ``TOPIC_ID_INVALID`` for ``GetRepliesRequest``. We scan recent group history instead.

    Matching (first wins):
    1. ``MessageReplyHeader.reply_to_msg_id == ping_message_id`` (direct reply to our ping)
    2. Same sender and ``reply_to_top_id`` equals ``topic_id`` or ``top_message_id``
       (forum thread match when the bot does not quote our message id by number)
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(2)
        best_loose = None
        async for msg in client.iter_messages(group, limit=50):
            if msg.id <= ping_message_id:
                continue
            sender = await msg.get_sender()
            if not sender or not hasattr(sender, "username") or sender.username != bot_username:
                continue
            r = msg.reply_to
            if isinstance(r, MessageReplyHeader):
                if r.reply_to_msg_id == ping_message_id:
                    return msg.text or ""
                tops = [x for x in (topic_id, top_message_id) if x is not None]
                if tops and r.reply_to_top_id in tops:
                    return msg.text or ""
            if best_loose is None or msg.id < best_loose.id:
                best_loose = msg
        if best_loose is not None:
            return best_loose.text or ""
    return None


async def send_in_topic(
    client: TelegramClient,
    group,
    text: str,
    top_message_id: int,
):
    """Send ``text`` into the forum thread (reply chain) anchored at ``top_message_id``."""
    return await client.send_message(group, text, reply_to=top_message_id)
