"""Load configuration from environment (no secrets in source control)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class TelethonEnvConfig:
    """Credentials and paths for Telethon (human MTProto session)."""

    api_id: int
    api_hash: str
    phone: str
    session_path: Path
    group_id: int
    otp_code_file: Path
    gasclaw_bot: str
    minimax_bot: str


def load_telethon_env() -> TelethonEnvConfig:
    """Load required Telethon settings from the environment."""
    api_id_raw = os.environ.get("TELEGRAM_API_ID", "").strip()
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    phone = os.environ.get("TELEGRAM_PHONE", "").strip()
    group_raw = os.environ.get("TELEGRAM_GROUP_ID", "").strip()
    session_raw = os.environ.get(
        "TELETHON_SESSION_PATH",
        str(_repo_root() / "data" / "tg_session"),
    ).strip()
    otp_file = os.environ.get("TELEGRAM_OTP_CODE_FILE", "/tmp/tg_otp_code").strip()
    gasclaw = os.environ.get("TELEGRAM_TEST_GASCLAW_BOT", "gasclaw_master_bot").strip()
    minimax = os.environ.get("TELEGRAM_TEST_MINIMAX_BOT", "minimax_gastown_publish_bot").strip()

    missing = [
        name
        for name, val in [
            ("TELEGRAM_API_ID", api_id_raw),
            ("TELEGRAM_API_HASH", api_hash),
            ("TELEGRAM_PHONE", phone),
            ("TELEGRAM_GROUP_ID", group_raw),
        ]
        if not val
    ]
    if missing:
        raise SystemExit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + "\nSee .env.example and README.md"
        )

    try:
        api_id = int(api_id_raw)
    except ValueError as e:
        raise SystemExit(f"TELEGRAM_API_ID must be an integer, got {api_id_raw!r}") from e

    try:
        group_id = int(group_raw)
    except ValueError as e:
        raise SystemExit(f"TELEGRAM_GROUP_ID must be an integer, got {group_raw!r}") from e

    session_path = Path(session_raw).expanduser()
    session_path.parent.mkdir(parents=True, exist_ok=True)

    return TelethonEnvConfig(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        session_path=session_path,
        group_id=group_id,
        otp_code_file=Path(otp_file).expanduser(),
        gasclaw_bot=gasclaw,
        minimax_bot=minimax,
    )


@dataclass(frozen=True)
class BotSuiteEntry:
    username: str
    label: str
    spawn_agent: str


def load_bot_suite(path: Path | None = None) -> tuple[int, dict[str, BotSuiteEntry]]:
    """Load multi-bot suite from JSON. Defaults to examples/bots.example.json."""
    root = _repo_root()
    cfg_path = path or Path(
        os.environ.get("TELETHON_BOTS_CONFIG", str(root / "examples" / "bots.example.json"))
    ).expanduser()

    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    group_id = int(raw["group_id"])
    bots: dict[str, BotSuiteEntry] = {}
    for username, meta in raw["bots"].items():
        bots[username] = BotSuiteEntry(
            username=username,
            label=str(meta["label"]),
            spawn_agent=str(meta["spawn_agent"]),
        )
    return group_id, bots
