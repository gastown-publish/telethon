"""Offline tests for forum thread matching (no Telegram)."""

from __future__ import annotations

from types import SimpleNamespace

from telethon.tl.types import MessageReplyHeader

from gastown_telethon.forum import _in_same_forum_thread_as_ping


def _hdr(
    *,
    reply_to_msg_id: int | None = None,
    reply_to_top_id: int | None = None,
) -> MessageReplyHeader:
    return MessageReplyHeader(
        reply_to_msg_id=reply_to_msg_id,
        reply_to_top_id=reply_to_top_id,
    )


def test_direct_reply_to_ping_matches() -> None:
    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msg = SimpleNamespace(reply_to=_hdr(reply_to_msg_id=100, reply_to_top_id=5000))
    assert _in_same_forum_thread_as_ping(sent, msg) is True


def test_same_top_id_matches() -> None:
    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msg = SimpleNamespace(reply_to=_hdr(reply_to_msg_id=99, reply_to_top_id=5000))
    assert _in_same_forum_thread_as_ping(sent, msg) is True


def test_different_top_id_rejects() -> None:
    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msg = SimpleNamespace(reply_to=_hdr(reply_to_msg_id=99, reply_to_top_id=6000))
    assert _in_same_forum_thread_as_ping(sent, msg) is False


def test_fallback_top_message_id_when_sent_has_no_reply_header() -> None:
    sent = SimpleNamespace(id=100, reply_to=None)
    msg = SimpleNamespace(reply_to=_hdr(reply_to_msg_id=99, reply_to_top_id=7777))
    assert _in_same_forum_thread_as_ping(sent, msg, top_message_id=7777) is True
    assert _in_same_forum_thread_as_ping(sent, msg, top_message_id=8888) is False


def test_no_reply_header_on_bot_message_rejects() -> None:
    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msg = SimpleNamespace(reply_to=None)
    assert _in_same_forum_thread_as_ping(sent, msg) is False
