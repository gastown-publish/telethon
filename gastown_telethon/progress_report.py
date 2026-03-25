"""Validate hourly progress replies (measurable template, not one-word OK)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Bot sometimes posts OpenClaw error text instead of a real answer — never treat as success.
_INFRA_FAILURE_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    ("kimi-coding", "forbidden route kimi-coding (use moonshot/minimax-m2.5 via LiteLLM)"),
    ("k2p5", "forbidden model id k2p5"),
    ("authentication_error", "upstream authentication_error"),
    ("http 401", "HTTP 401 from model provider"),
    ("agent failed before reply", "OpenClaw agent failed before reply"),
    ("all models failed", "all configured models failed"),
    ("no api key found for provider", "missing provider API key / auth"),
)

_PLACEHOLDER_OK = re.compile(
    r"^\s*(ok|okay|yes|done|👍|✅)\s*\.?\s*$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ProgressReportRules:
    min_chars: int
    """Heading keywords must appear inside ``## ...`` lines (substring match)."""
    required_heading_keywords: tuple[str, ...]


def reply_indicates_infrastructure_failure(text: str) -> tuple[bool, str]:
    """True if the bot message is an error stub (Kimi route, 401, agent failed, etc.)."""
    t = text.lower()
    for needle, reason in _INFRA_FAILURE_SUBSTRINGS:
        if needle.lower() in t:
            return True, reason
    return False, ""


def validate_hourly_progress_reply(
    text: str | None,
    *,
    rules: ProgressReportRules | None = None,
) -> tuple[bool, list[str]]:
    """Return (ok, error_messages)."""
    r = rules or ProgressReportRules(
        min_chars=180,
        required_heading_keywords=("past", "repo", "measurable", "improvement"),
    )
    errors: list[str] = []
    if text is None:
        return False, ["empty reply"]

    s = text.strip()
    if not s:
        return False, ["empty reply"]

    bad, why = reply_indicates_infrastructure_failure(s)
    if bad:
        return False, [f"bot reply is a failure/error message, not a valid report: {why}"]

    if _PLACEHOLDER_OK.match(s):
        return False, ["reply is only OK/yes — use the full Markdown template from the prompt"]

    if len(s) < r.min_chars:
        errors.append(f"too short ({len(s)} chars; minimum {r.min_chars})")

    headings = re.findall(r"(?m)^##\s+(.+)$", s)
    if len(headings) < 3:
        errors.append(f"need at least 3 lines like '## Section' (found {len(headings)} heading line(s))")

    headings_blob = " ".join(headings).lower()
    for kw in r.required_heading_keywords:
        if kw.lower() not in headings_blob:
            errors.append(f"no ## heading covers {kw!r} (add a section, e.g. '## Past hour — repo')")

    # Measurable repo signal: numbers or explicit git/CI tokens
    if not re.search(r"\b(\d{1,4}|commits?|pull\s*requests?|prs?|merged|workflow|ci\b)", s, re.I):
        errors.append("add measurable signals: commit/PR counts, SHAs, or CI status")

    return (len(errors) == 0, errors)


def rules_from_config(
    min_chars: int | None,
    heading_keywords: list[str] | tuple[str, ...] | None,
) -> ProgressReportRules:
    return ProgressReportRules(
        min_chars=int(min_chars) if min_chars is not None else 180,
        required_heading_keywords=tuple(x.lower() for x in heading_keywords)
        if heading_keywords
        else ("past", "repo", "measurable", "improvement"),
    )
