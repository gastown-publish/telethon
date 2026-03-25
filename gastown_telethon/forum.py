"""Forum (topic) helpers for Telegram supergroups."""

from __future__ import annotations

import asyncio
import time

from telethon import TelegramClient
from telethon.tl import functions
from telethon.tl.types import ForumTopic, ForumTopicDeleted, MessageReplyHeader


def _in_same_forum_thread_as_ping(
    sent,
    msg,
    *,
    top_message_id: int | None = None,
) -> bool:
    """True if ``msg`` belongs to the same forum thread as ``sent`` (the health ping).

    ``top_message_id`` is the forum topic anchor from ``GetForumTopicsByID``; pass it when
    ``sent.reply_to`` may be missing so we can still match ``reply_to_top_id`` on the bot reply.
    """
    mr = msg.reply_to
    if not isinstance(mr, MessageReplyHeader):
        return False
    if mr.reply_to_msg_id == sent.id:
        return True
    sr = sent.reply_to
    if isinstance(sr, MessageReplyHeader):
        if sr.reply_to_top_id is not None and mr.reply_to_top_id is not None:
            return sr.reply_to_top_id == mr.reply_to_top_id
        return False
    if top_message_id is not None and mr.reply_to_top_id is not None:
        return mr.reply_to_top_id == top_message_id
    return False


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
    sent,
    *,
    top_message_id: int | None = None,
    timeout: float = 90.0,
) -> str | None:
    """Wait for a reply from ``bot_username`` **in the same forum thread** as ``sent``.

    We cannot use ``iter_messages(..., reply_to=top_msg)`` on forums — Telegram returns
    ``TOPIC_ID_INVALID`` for ``GetRepliesRequest``. We scan recent group history instead.

    Only messages that pass :func:`_in_same_forum_thread_as_ping` are considered — this avoids
    attributing another topic’s bot activity to the wrong health check.
    """
    ping_id = sent.id
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(2)
        earliest: tuple[int, str] | None = None
        async for msg in client.iter_messages(group, limit=50, min_id=ping_id):
            if msg.id <= ping_id:
                continue
            sender = await msg.get_sender()
            if not sender or not hasattr(sender, "username") or sender.username != bot_username:
                continue
            if not _in_same_forum_thread_as_ping(sent, msg, top_message_id=top_message_id):
                continue
            text = msg.text or ""
            if earliest is None or msg.id < earliest[0]:
                earliest = (msg.id, text)
        if earliest is not None:
            return earliest[1]
    return None


async def send_in_topic(
    client: TelegramClient,
    group,
    text: str,
    top_message_id: int,
):
    """Send ``text`` into the forum thread (reply chain) anchored at ``top_message_id``."""
    return await client.send_message(group, text, reply_to=top_message_id)
