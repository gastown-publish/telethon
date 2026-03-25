"""Tests: forum topic list is sorted, unique, and one bot per topic (room organization)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gastown_telethon.forum_config import (
    ForumTopicSpec,
    load_forum_health_config,
    validate_forum_topic_layout,
)


def test_validate_accepts_sorted_unique_topics() -> None:
    topics = [
        ForumTopicSpec(918, "bot_a", "a", False, ""),
        ForumTopicSpec(919, "bot_b", "b", False, ""),
    ]
    validate_forum_topic_layout(topics)


def test_validate_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_forum_topic_layout([])


def test_validate_rejects_unsorted_topic_ids() -> None:
    topics = [
        ForumTopicSpec(920, "a", "a", False, ""),
        ForumTopicSpec(918, "b", "b", False, ""),
    ]
    with pytest.raises(ValueError, match="sorted"):
        validate_forum_topic_layout(topics)


def test_validate_rejects_duplicate_topic_id() -> None:
    topics = [
        ForumTopicSpec(918, "bot_a", "a", False, ""),
        ForumTopicSpec(918, "bot_b", "b", False, ""),
    ]
    with pytest.raises(ValueError, match="duplicate topic_id"):
        validate_forum_topic_layout(topics)


def test_validate_rejects_duplicate_bot_username() -> None:
    topics = [
        ForumTopicSpec(918, "same_bot", "a", False, ""),
        ForumTopicSpec(919, "same_bot", "b", False, ""),
    ]
    with pytest.raises(ValueError, match="duplicate bot_username"):
        validate_forum_topic_layout(topics)


def test_validate_bot_username_case_insensitive_duplicate() -> None:
    topics = [
        ForumTopicSpec(918, "MyBot", "a", False, ""),
        ForumTopicSpec(919, "mybot", "b", False, ""),
    ]
    with pytest.raises(ValueError, match="duplicate bot_username"):
        validate_forum_topic_layout(topics)


def test_example_json_topics_are_organized() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = load_forum_health_config(root / "examples" / "forum_health.example.json")
    ids = [t.topic_id for t in cfg.topics]
    assert ids == [918, 919, 920, 921]
    assert len({t.bot_username.lower() for t in cfg.topics}) == 4
    assert [t.label for t in cfg.topics] == ["gasclaw", "minimax", "gasskill", "management"]
    optional = [t.optional for t in cfg.topics]
    assert optional == [False, False, False, True]


def test_load_rejects_bad_file(tmp_path: Path) -> None:
    bad = {
        "group_id": -1,
        "topics": [
            {"topic_id": 919, "bot_username": "x", "label": "x"},
            {"topic_id": 918, "bot_username": "y", "label": "y"},
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="sorted"):
        load_forum_health_config(p)
