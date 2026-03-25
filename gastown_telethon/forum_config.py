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


@dataclass(frozen=True)
class ForumHealthConfig:
    group_id: int
    ping_message: str
    reply_timeout_sec: float
    topics: list[ForumTopicSpec]


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
        )
        for t in data["topics"]
    ]
    return ForumHealthConfig(
        group_id=int(data["group_id"]),
        ping_message=str(data.get("ping_message", "[health] ping")),
        reply_timeout_sec=float(data.get("reply_timeout_sec", 45)),
        topics=topics,
    )
