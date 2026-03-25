"""Tests for wait_for_bot_reply_to_ping with a fake client (no Telegram)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from telethon.tl.types import MessageReplyHeader

from gastown_telethon import forum as forum_mod
from gastown_telethon.forum import wait_for_bot_reply_to_ping


def _hdr(**kwargs) -> MessageReplyHeader:
    return MessageReplyHeader(
        reply_to_msg_id=kwargs.get("reply_to_msg_id"),
        reply_to_top_id=kwargs.get("reply_to_top_id"),
    )


class _FakeMsg:
    __slots__ = ("id", "reply_to", "text", "_username")

    def __init__(self, id: int, username: str, reply_to: MessageReplyHeader, text: str = "ok"):
        self.id = id
        self.reply_to = reply_to
        self.text = text
        self._username = username

    async def get_sender(self):
        return SimpleNamespace(username=self._username)


def test_wait_returns_earliest_matching_reply() -> None:
    asyncio.run(_async_returns_earliest())


async def _async_returns_earliest() -> None:
    async def no_sleep(_t: float) -> None:
        return None

    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msgs = [
        _FakeMsg(103, "other_bot", _hdr(reply_to_top_id=5000), "noise"),
        _FakeMsg(104, "target_bot", _hdr(reply_to_msg_id=100), "first"),
        _FakeMsg(105, "target_bot", _hdr(reply_to_msg_id=100), "second"),
    ]

    class FakeClient:
        async def iter_messages(self, _group, **kwargs):
            for m in msgs:
                yield m

    orig_sleep = forum_mod.asyncio.sleep
    try:
        forum_mod.asyncio.sleep = no_sleep  # type: ignore[method-assign]
        out = await wait_for_bot_reply_to_ping(
            FakeClient(),
            object(),
            "target_bot",
            sent,
            top_message_id=None,
            timeout=5.0,
        )
        assert out == "first"
    finally:
        forum_mod.asyncio.sleep = orig_sleep  # type: ignore[method-assign]


def test_wait_returns_none_when_only_wrong_thread() -> None:
    asyncio.run(_async_only_wrong_thread())


async def _async_only_wrong_thread() -> None:
    async def no_sleep(_t: float) -> None:
        return None

    sent = SimpleNamespace(id=100, reply_to=_hdr(reply_to_top_id=5000))
    msgs = [
        _FakeMsg(104, "target_bot", _hdr(reply_to_top_id=9999), "wrong thread"),
    ]

    class FakeClient:
        async def iter_messages(self, _group, **kwargs):
            for m in msgs:
                yield m

    call = {"n": 0}

    def time_side_effect() -> float:
        call["n"] += 1
        if call["n"] == 1:
            return 0.0
        return 1e9

    orig_sleep = forum_mod.asyncio.sleep
    orig_time = forum_mod.time.time
    try:
        forum_mod.asyncio.sleep = no_sleep  # type: ignore[method-assign]
        forum_mod.time.time = time_side_effect  # type: ignore[method-assign]
        out = await wait_for_bot_reply_to_ping(
            FakeClient(),
            object(),
            "target_bot",
            sent,
            top_message_id=5000,
            timeout=0.01,
        )
        assert out is None
    finally:
        forum_mod.asyncio.sleep = orig_sleep  # type: ignore[method-assign]
        forum_mod.time.time = orig_time  # type: ignore[method-assign]
