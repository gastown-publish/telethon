"""Shared Telethon helpers for integration tests."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from telethon import TelegramClient


async def wait_for_bot_reply(client, group, bot_username: str, timeout: float = 30):
    """Wait for a new reply from ``bot_username`` in ``group``."""
    deadline = time.time() + timeout
    seen_ids: set[int] = set()

    async for msg in client.iter_messages(group, limit=3):
        seen_ids.add(msg.id)

    while time.time() < deadline:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(group, limit=5):
            if msg.id not in seen_ids:
                sender = await msg.get_sender()
                if sender and hasattr(sender, "username") and sender.username == bot_username:
                    return msg.text
                seen_ids.add(msg.id)
    return None


async def wait_reply_after_baseline(client, group, bot_username: str, timeout: float = 30):
    """Same as wait_for_bot_reply (baseline then poll)."""
    return await wait_for_bot_reply(client, group, bot_username, timeout=timeout)


async def get_reply_after_id(client, group, bot_username: str, after_id: int, timeout: float = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(3)
        async for msg in client.iter_messages(group, limit=10):
            if msg.id <= after_id:
                break
            sender = await msg.get_sender()
            if sender and hasattr(sender, "username") and sender.username == bot_username:
                return msg.text
    return None


async def otp_from_file(code_file: Path):
    """Poll ``code_file`` for a numeric OTP (non-interactive login)."""

    print(f"⏳ Waiting for OTP code in {code_file} ...")
    print(f"   Write it with: echo 12345 > {code_file}")
    while True:
        try:
            code = code_file.read_text(encoding="utf-8").strip()
            if code and code.isdigit():
                code_file.unlink(missing_ok=True)
                print(f"✅ Got code: {code}")
                return code
        except FileNotFoundError:
            pass
        await asyncio.sleep(1)


def load_dotenv_if_present() -> None:
    """Load `.env` from repo root if ``python-dotenv`` is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parent.parent / ".env"
    if root.is_file():
        load_dotenv(root)
