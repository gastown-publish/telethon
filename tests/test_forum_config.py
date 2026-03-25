"""Offline tests for forum health JSON."""

from __future__ import annotations

from pathlib import Path

from gastown_telethon.forum_config import load_forum_health_config


def test_load_forum_health_example() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = load_forum_health_config(root / "examples" / "forum_health.example.json")
    assert cfg.group_id == -1003810709807
    assert len(cfg.topics) == 4
    labels = {t.label for t in cfg.topics}
    assert "management" in labels
    mgmt = [t for t in cfg.topics if t.label == "management"][0]
    assert mgmt.optional is True
    assert cfg.reply_timeout_sec >= 10
