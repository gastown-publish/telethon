"""Offline tests: no Telegram credentials or network required."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gastown_telethon.config import load_bot_suite


def test_load_bot_suite_example(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    example = root / "examples" / "bots.example.json"
    group_id, bots = load_bot_suite(example)
    assert group_id < 0
    assert "gasclaw_master_bot" in bots
    assert bots["gasclaw_master_bot"].spawn_agent == "crew-1"
    assert len(bots) >= 3


def test_load_telethon_env_requires_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    from gastown_telethon import config as cfg_mod

    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    monkeypatch.delenv("TELEGRAM_PHONE", raising=False)
    monkeypatch.delenv("TELEGRAM_GROUP_ID", raising=False)

    with pytest.raises(SystemExit) as exc:
        cfg_mod.load_telethon_env()
    assert "TELEGRAM_API_ID" in str(exc.value) or "Missing" in str(exc.value)


def test_load_telethon_env_parses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gastown_telethon import config as cfg_mod

    session_base = tmp_path / "sess"
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    monkeypatch.setenv("TELEGRAM_PHONE", "+10000000000")
    monkeypatch.setenv("TELEGRAM_GROUP_ID", "-1003810709807")
    monkeypatch.setenv("TELETHON_SESSION_PATH", str(session_base))

    c = cfg_mod.load_telethon_env()
    assert c.api_id == 12345
    assert c.group_id == -1003810709807
    assert c.session_path == session_base


def test_helpers_wait_for_bot_reply_signature() -> None:
    from gastown_telethon.helpers import get_reply_after_id, wait_for_bot_reply

    assert callable(wait_for_bot_reply)
    assert callable(get_reply_after_id)
