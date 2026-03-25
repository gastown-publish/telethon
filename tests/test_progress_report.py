"""Offline tests for hourly progress reply validation."""

from __future__ import annotations

from gastown_telethon.progress_report import ProgressReportRules, validate_hourly_progress_reply


def _good() -> str:
    return """## Past hour — repo
- Repo: gastown-publish/gasclaw
- Commits: abc1234 (fix tests)
- PRs: #42 merged
- CI: unit-tests pass

## Measurable
- Commits: 2 | PRs opened: 0 | PRs merged: 1 | Issues closed: 0

## Work done
- Fixed flaky test

## Blockers
- None

## Next hour
- Continue CI hardening

## Improvement
- Run pytest locally before push
"""


def test_accepts_substantive_template() -> None:
    ok, errs = validate_hourly_progress_reply(_good())
    assert ok, errs


def test_rejects_ok() -> None:
    ok, errs = validate_hourly_progress_reply("OK")
    assert not ok
    assert any("OK" in e or "placeholder" in e.lower() for e in errs)


def test_rejects_too_short() -> None:
    rules = ProgressReportRules(min_chars=500, required_heading_keywords=("past", "repo", "measurable", "improvement"))
    ok, errs = validate_hourly_progress_reply(_good()[:80], rules=rules)
    assert not ok


def test_rejects_missing_headings() -> None:
    ok, errs = validate_hourly_progress_reply(
        "some long text " * 40 + " commits 1 pr 2 merged ci ok measurable improvement past repo"
    )
    assert not ok
