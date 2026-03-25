"""Exercise every bot in ``examples/bots.example.json`` (or ``TELETHON_BOTS_CONFIG``): ping, /subagents, spawn, list, ignore."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from telethon import TelegramClient

from gastown_telethon.config import load_bot_suite, load_telethon_env
from gastown_telethon.helpers import load_dotenv_if_present, otp_from_file, wait_for_bot_reply

PASS = 0
FAIL = 0
RESULTS: list[str] = []


def report(name: str, passed: bool, detail: str = "") -> None:
    global PASS, FAIL
    if passed:
        PASS += 1
        RESULTS.append(f"  ✅ {name}")
    else:
        FAIL += 1
        RESULTS.append(f"  ❌ {name}: {detail}")


async def async_main() -> bool:
    load_dotenv_if_present()
    cfg = load_telethon_env()
    config_path = os.environ.get("TELETHON_BOTS_CONFIG")
    group_id, bots = load_bot_suite(Path(config_path) if config_path else None)

    if group_id != cfg.group_id:
        print(
            f"⚠️  TELEGRAM_GROUP_ID ({cfg.group_id}) != bots config group_id ({group_id}); using bots file group.",
            file=sys.stderr,
        )

    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    async def get_code():
        return await otp_from_file(cfg.otp_code_file)

    await client.start(phone=cfg.phone, code_callback=get_code)
    group = await client.get_entity(group_id)

    print("=" * 60)
    print("  ALL BOTS INTEGRATION TEST")
    print("=" * 60)

    for bot_name, entry in bots.items():
        print(f"\n--- {entry.label} (@{bot_name}) ---")

        print("  🧪 @mention response...")
        await client.send_message(group, f"@{bot_name} ping")
        reply = await wait_for_bot_reply(client, group, bot_name, timeout=30)
        report(f"{entry.label}: responds to @mention", reply is not None, "no reply")
        if reply:
            print(f"     → {reply[:60]}...")
        await asyncio.sleep(5)

        print("  🧪 /subagents menu...")
        await client.send_message(group, f"/subagents@{bot_name}")
        reply = await wait_for_bot_reply(client, group, bot_name, timeout=20)
        report(
            f"{entry.label}: /subagents",
            reply is not None and "spawn" in (reply or "").lower(),
            (reply or "no reply")[:60],
        )
        if reply:
            print(f"     → {reply[:60]}...")
        await asyncio.sleep(5)

        agent = entry.spawn_agent
        print(f"  🧪 spawn {agent}...")
        await client.send_message(
            group,
            f"/subagents@{bot_name} spawn {agent} Check the repo status with gh issue list and summarize",
        )
        reply = await wait_for_bot_reply(client, group, bot_name, timeout=45)
        ok = (
            reply
            and "spawn" in reply.lower()
            and "fail" not in reply.lower()
            and "not allowed" not in reply.lower()
        )
        report(f"{entry.label}: spawn {agent}", bool(ok), (reply or "no reply")[:60])
        if reply:
            print(f"     → {reply[:60]}...")
        await asyncio.sleep(5)

        print("  🧪 /subagents list...")
        await client.send_message(group, f"/subagents@{bot_name} list")
        reply = await wait_for_bot_reply(client, group, bot_name, timeout=20)
        report(
            f"{entry.label}: /subagents list",
            reply is not None
            and (
                "subagent" in (reply or "").lower()
                or "active" in (reply or "").lower()
                or "running" in (reply or "").lower()
            ),
            (reply or "no reply")[:60],
        )
        if reply:
            print(f"     → {reply[:80]}...")
        await asyncio.sleep(8)

    print("\n--- Non-mention test (all bots) ---")
    print("  🧪 bots ignore non-mentioned message...")
    last_id = 0
    async for msg in client.iter_messages(group, limit=1):
        last_id = msg.id
    await asyncio.sleep(10)
    await client.send_message(group, "random message nobody should reply to this")
    await asyncio.sleep(20)
    found = False
    bot_names = set(bots.keys())
    async for msg in client.iter_messages(group, limit=5):
        if msg.id <= last_id:
            break
        if msg.text and "random message" in msg.text:
            continue
        sender = await msg.get_sender()
        if sender and hasattr(sender, "username") and sender.username in bot_names:
            found = True
            break
    report("all bots ignore non-mentioned", not found, "a bot replied")

    print()
    print("=" * 60)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    print("=" * 60)
    for r in RESULTS:
        print(r)

    await client.disconnect()
    return FAIL == 0


def main() -> None:
    ok = asyncio.run(async_main())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
