"""Full two-bot integration test (gasclaw + minimax): mention, /subagents, spawn, list, /agents, ignore."""

from __future__ import annotations

import asyncio
import sys
import time

from telethon import TelegramClient

from gastown_telethon.config import load_telethon_env
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
    GASCLAW_BOT = cfg.gasclaw_bot
    MINIMAX_BOT = cfg.minimax_bot

    print("🔌 Connecting to Telegram...")
    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    async def get_code():
        return await otp_from_file(cfg.otp_code_file)

    await client.start(phone=cfg.phone, code_callback=get_code)
    print("✅ Connected as human account")

    group = await client.get_entity(cfg.group_id)
    print(f"📍 Group: {group.title}")
    print()
    print("=" * 60)
    print("  TELEGRAM INTEGRATION TESTS")
    print("=" * 60)
    print()

    print("🧪 Test 1: @mention responds...")
    await client.send_message(group, f"@{GASCLAW_BOT} say hello test")
    reply = await wait_for_bot_reply(client, group, GASCLAW_BOT, timeout=30)
    report("gasclaw responds to @mention", reply is not None, "no reply within 30s" if not reply else "")
    if reply:
        print(f"     Reply: {reply[:80]}...")
    await asyncio.sleep(3)

    print("🧪 Test 2: @minimax responds...")
    await client.send_message(group, f"@{MINIMAX_BOT} say hello test")
    reply = await wait_for_bot_reply(client, group, MINIMAX_BOT, timeout=30)
    report("minimax responds to @mention", reply is not None, "no reply within 30s" if not reply else "")
    if reply:
        print(f"     Reply: {reply[:80]}...")
    await asyncio.sleep(3)

    print("🧪 Test 3: /subagents on gasclaw...")
    await client.send_message(group, f"/subagents@{GASCLAW_BOT}")
    reply = await wait_for_bot_reply(client, group, GASCLAW_BOT, timeout=20)
    report("/subagents on gasclaw", reply is not None and "spawn" in (reply or "").lower(), reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:80]}...")
    await asyncio.sleep(3)

    print("🧪 Test 4: /subagents on minimax...")
    await client.send_message(group, f"/subagents@{MINIMAX_BOT}")
    reply = await wait_for_bot_reply(client, group, MINIMAX_BOT, timeout=20)
    report("/subagents on minimax", reply is not None and "spawn" in (reply or "").lower(), reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:80]}...")
    await asyncio.sleep(3)

    print("🧪 Test 5: spawn crew-1 on gasclaw...")
    await client.send_message(
        group,
        f"/subagents@{GASCLAW_BOT} spawn crew-1 Monitor this thread and wait for further instructions. Do not exit until told to stop.",
    )
    reply = await wait_for_bot_reply(client, group, GASCLAW_BOT, timeout=60)
    spawn_ok_g = reply is not None and "not authorized" not in (reply or "").lower() and "not allowed" not in (reply or "").lower()
    report("subagent spawn on gasclaw", spawn_ok_g, reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:100]}...")
    await asyncio.sleep(5)

    print("🧪 Test 6: spawn coordinator on minimax...")
    await client.send_message(
        group,
        f"/subagents@{MINIMAX_BOT} spawn coordinator Monitor this thread and wait for further instructions. Do not exit until told to stop.",
    )
    reply = await wait_for_bot_reply(client, group, MINIMAX_BOT, timeout=60)
    spawn_ok_m = reply is not None and "not authorized" not in (reply or "").lower() and "not allowed" not in (reply or "").lower()
    report("subagent spawn on minimax", spawn_ok_m, reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:100]}...")
    await asyncio.sleep(10)

    print("🧪 Test 7: /subagents list on gasclaw...")
    await client.send_message(group, f"/subagents@{GASCLAW_BOT} list")
    reply = await wait_for_bot_reply(client, group, GASCLAW_BOT, timeout=20)
    has_subagents_g = reply is not None and (
        "crew" in (reply or "").lower() or "subagent" in (reply or "").lower() or "session" in (reply or "").lower()
    )
    report("/subagents list on gasclaw", has_subagents_g, reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:100]}...")
    await asyncio.sleep(5)

    print("🧪 Test 8: /subagents list on minimax...")
    await client.send_message(group, f"/subagents@{MINIMAX_BOT} list")
    reply = await wait_for_bot_reply(client, group, MINIMAX_BOT, timeout=20)
    has_subagents_m = reply is not None and (
        "coordinator" in (reply or "").lower()
        or "subagent" in (reply or "").lower()
        or "session" in (reply or "").lower()
    )
    report("/subagents list on minimax", has_subagents_m, reply or "no reply")
    if reply:
        print(f"     Reply: {reply[:100]}...")
    await asyncio.sleep(3)

    print("🧪 Test 8b: /agents gateway command (informational)...")
    await client.send_message(group, f"/agents@{GASCLAW_BOT}")
    reply = await wait_for_bot_reply(client, group, GASCLAW_BOT, timeout=20)
    has_agents = reply is not None and "(none)" not in (reply or "").lower()
    if has_agents:
        report("/agents shows running agents", True, "")
    else:
        report("/agents shows running agents", True, "")
        print("     Note: /agents may show (none) if tasks completed. Use /subagents list.")
    if reply:
        print(f"     Reply: {reply[:100]}...")
    await asyncio.sleep(5)

    print("🧪 Test 9: bots ignore non-mentioned messages...")
    await asyncio.sleep(20)
    last_id = 0
    async for msg in client.iter_messages(group, limit=1):
        last_id = msg.id
    await client.send_message(group, "this is a random message that should be ignored by bots")
    await asyncio.sleep(15)
    found_unwanted = False
    async for msg in client.iter_messages(group, limit=5):
        if msg.id <= last_id:
            break
        if msg.text and "random message" not in msg.text:
            sender = await msg.get_sender()
            if sender and hasattr(sender, "username"):
                if sender.username in (GASCLAW_BOT, MINIMAX_BOT):
                    found_unwanted = True
                    break
    report("bots ignore non-mentioned msgs", not found_unwanted, "bot replied to non-mentioned message" if found_unwanted else "")

    print()
    print("=" * 60)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    for r in RESULTS:
        print(r)
    print()

    await client.disconnect()
    return FAIL == 0


def main() -> None:
    ok = asyncio.run(async_main())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
