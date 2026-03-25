"""Reject bot replies that are OpenClaw/model error stubs."""

from __future__ import annotations

from gastown_telethon.progress_report import reply_indicates_infrastructure_failure, validate_hourly_progress_reply


def test_rejects_kimi_coding_error() -> None:
    msg = (
        "⚠️ Agent failed before reply: All models failed (2): kimi-coding/k2p5: HTTP 401 authentication_error"
    )
    bad, _ = reply_indicates_infrastructure_failure(msg)
    assert bad
    ok, errs = validate_hourly_progress_reply(msg)
    assert not ok
    assert any("failure" in e.lower() or "kimi" in e.lower() for e in errs)


def test_rejects_all_models_failed() -> None:
    msg = "All models failed: moonshot/minimax-m2.5: connection refused"
    bad, _ = reply_indicates_infrastructure_failure(msg)
    assert bad


def test_accepts_real_template_still() -> None:
    good = """## Past hour — repo
- Repo: gastown-publish/x
- Commits: abc
- PRs: #1
- CI: pass

## Measurable
- Commits: 1 | PRs: 0

## Work done
- stuff

## Blockers
- none

## Next hour
- more

## Improvement
- test before push
"""
    ok, errs = validate_hourly_progress_reply(good)
    assert ok, errs
