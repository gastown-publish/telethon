"""Load forum health monitor JSON config."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ForumTopicSpec:
    topic_id: int
    bot_username: str
    label: str
    optional: bool = False
    description: str = ""


@dataclass(frozen=True)
class ForumHealthConfig:
    group_id: int
    ping_message: str
    reply_timeout_sec: float
    topics: list[ForumTopicSpec]
    min_reply_chars: int = 180
    progress_heading_keywords: tuple[str, ...] = ("past", "repo", "measurable", "improvement")


def validate_forum_topic_layout(topics: list[ForumTopicSpec]) -> None:
    """Ensure forum health config stays organized: one topic id and one bot per row, sorted order.

    - **Sorted** ``topic_id`` ascending (stable ping order, matches docs 918→921).
    - **No duplicate** ``topic_id`` (each forum thread appears once).
    - **No duplicate** ``bot_username`` (each bot is responsible for exactly one topic in this check).
    """
    if not topics:
        raise ValueError("forum_health: topics list is empty")
    ids = [t.topic_id for t in topics]
    if ids != sorted(ids):
        raise ValueError(
            f"forum_health: topics must be sorted by topic_id ascending; got {ids!r}"
        )
    if len(set(ids)) != len(ids):
        raise ValueError("forum_health: duplicate topic_id in topics")
    names = [t.bot_username.lower() for t in topics]
    if len(set(names)) != len(names):
        raise ValueError("forum_health: duplicate bot_username in topics")


def load_forum_health_config(path: Path | None = None) -> ForumHealthConfig:
    raw_path = path or os.environ.get("TELETHON_FORUM_HEALTH_CONFIG")
    if raw_path:
        p = Path(raw_path).expanduser()
    else:
        p = _repo_root() / "examples" / "forum_health.example.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    topics = [
        ForumTopicSpec(
            topic_id=int(t["topic_id"]),
            bot_username=str(t["bot_username"]),
            label=str(t["label"]),
            optional=bool(t.get("optional", False)),
            description=str(t.get("description", "")),
        )
        for t in data["topics"]
    ]
    validate_forum_topic_layout(topics)
    kw = data.get("progress_heading_keywords")
    keywords = [str(x) for x in kw] if isinstance(kw, list) else None
    return ForumHealthConfig(
        group_id=int(data["group_id"]),
        ping_message=str(data.get("ping_message", "[health] ping")),
        reply_timeout_sec=float(data.get("reply_timeout_sec", 45)),
        topics=topics,
        min_reply_chars=int(data.get("min_reply_chars", 180)),
        progress_heading_keywords=tuple(keywords)
        if keywords
        else ("past", "repo", "measurable", "improvement"),
    )
