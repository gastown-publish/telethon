#!/usr/bin/env python3
"""Scan tracked files for accidental Telegram credentials (bot tokens, api_hash hex).

Exit 1 if suspicious patterns are found. Safe to run without .env or sessions.

Usage:
  python scripts/scan_credentials.py           # all git-tracked text files
  python scripts/scan_credentials.py --staged  # git diff --cached only (pre-commit)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Telegram bot token: numeric:id + ':' + 25+ alnum (typical ~35 chars secret part)
BOT_TOKEN_RE = re.compile(r"\b(\d{8,12}):([A-Za-z0-9_-]{25,})\b")
# api_hash from my.telegram.org is 32 lowercase hex
API_HASH_HEX_RE = re.compile(
    r'(?i)(api_hash|TELEGRAM_API_HASH)\s*[=:]\s*["\']?([a-f0-9]{32})["\']?'
)


def _git_tracked_files(repo_root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    paths = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        p = repo_root / line
        if p.is_file():
            paths.append(p)
    return paths


def _git_staged_files(repo_root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    )
    paths = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        p = repo_root / line
        if p.is_file():
            paths.append(p)
    return paths


def _should_skip(path: Path) -> bool:
    parts = path.parts
    if ".venv" in parts or "venv" in parts or "__pycache__" in parts:
        return True
    if path.suffix in {".png", ".jpg", ".ico", ".session"}:
        return True
    return False


def _is_placeholder_bot_token(match: re.Match[str]) -> bool:
    """Heuristic: example tokens in docs."""
    secret = match.group(2)
    if secret.lower().startswith("your") or "example" in secret.lower():
        return True
    if set(secret) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"):
        # All same char = placeholder
        if len(set(secret)) <= 2:
            return True
    return False


def _is_placeholder_hash(hex_str: str) -> bool:
    if hex_str in ("deadbeefdeadbeefdeadbeefdeadbeef", "your_api_hash_here"):
        return True
    if hex_str == "0" * 32:
        return True
    return False


def scan_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return errors

    for i, line in enumerate(text.splitlines(), 1):
        for m in BOT_TOKEN_RE.finditer(line):
            if _is_placeholder_bot_token(m):
                continue
            errors.append(f"{path}:{i}: possible Telegram bot token")
        for m in API_HASH_HEX_RE.finditer(line):
            hx = m.group(2)
            if _is_placeholder_hash(hx):
                continue
            # Real api_hash lines rarely appear in repo; flag unless clearly doc
            if ".example" in path.name or "scan_credentials" in str(path):
                continue
            errors.append(f"{path}:{i}: possible TELEGRAM api_hash (32 hex)")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Only scan files staged for commit",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    try:
        if args.staged:
            files = _git_staged_files(repo_root)
        else:
            files = _git_tracked_files(repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("scan_credentials: not a git repo or git failed; scanning Python tree only", file=sys.stderr)
        files = list((repo_root / "gastown_telethon").rglob("*.py"))

    all_errors: list[str] = []
    for f in sorted(files):
        if _should_skip(f):
            continue
        if f.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".example", ".sh"}:
            continue
        all_errors.extend(scan_file(f))

    if all_errors:
        print("Credential scan FAILED:", file=sys.stderr)
        for e in all_errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("Credential scan OK (no suspicious patterns in scanned files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
