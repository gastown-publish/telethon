"""Quick ping each bot (mention only), with cooldown between bots."""

from __future__ import annotations

import asyncio
import os
import sys

from telethon import TelegramClient

from gastown_telethon.config import load_telethon_env
from gastown_telethon.helpers import get_reply_after_id, load_dotenv_if_present, otp_from_file


def main() -> None:
    sys.exit(asyncio.run(async_main()))


async def async_main() -> int:
    load_dotenv_if_present()
    cfg = load_telethon_env()
    raw = os.environ.get(
        "TELEGRAM_TEST_PING_BOTS",
        "gasclaw_master_bot,minimax_gastown_publish_bot,gasskill_agent_bot",
    )
    bots = [b.strip() for b in raw.split(",") if b.strip()]

    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    async def get_code():
        return await otp_from_file(cfg.otp_code_file)

    await client.start(phone=cfg.phone, code_callback=get_code)
    group = await client.get_entity(cfg.group_id)

    print("=" * 60)
    print("  SIMPLE BOT TEST — ONE AT A TIME")
    print("=" * 60)

    results: list[str] = []
    passed = 0
    failed = 0

    for bot in bots:
        label = bot.split("_")[0]
        last_id = 0
        async for msg in client.iter_messages(group, limit=1):
            last_id = msg.id

        print(f"\n🧪 @{bot} ping...")
        await client.send_message(group, f"@{bot} ping")
        reply = await get_reply_after_id(client, group, bot, last_id, timeout=30)
        if reply:
            passed += 1
            results.append(f"  ✅ {label}: {reply[:50]}")
            print(f"   ✅ {reply[:60]}")
        else:
            failed += 1
            results.append(f"  ❌ {label}: no reply in 30s")
            print("   ❌ no reply")

        await asyncio.sleep(15)

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{passed + failed}")
    print(f"{'=' * 60}")
    for r in results:
        print(r)
    await client.disconnect()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    main()
