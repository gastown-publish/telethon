"""Ping each Gasclaw bot in its forum topic and verify a reply (human Telethon session)."""

from __future__ import annotations

import asyncio
import sys
import traceback

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from gastown_telethon.config import load_telethon_env
from gastown_telethon.forum import get_topic_top_message_id, send_in_topic, wait_for_bot_reply_to_ping
from gastown_telethon.forum_config import load_forum_health_config
from gastown_telethon.helpers import load_dotenv_if_present, otp_from_file


def _debug_hint(label: str, bot: str) -> str:
    return (
        f"  Debug ({label} / @{bot}): "
        "on the container host run: openclaw channels status --probe; "
        "openclaw doctor; check gateway process and ~/.openclaw/openclaw.json channels.telegram. "
        "See gasclaw-management HANDOFF.md for gateway ports."
    )


async def async_main() -> int:
    load_dotenv_if_present()
    cfg = load_telethon_env()
    fcfg = load_forum_health_config()

    if cfg.group_id != fcfg.group_id:
        print(
            f"⚠️  TELEGRAM_GROUP_ID ({cfg.group_id}) != forum_health.json group_id ({fcfg.group_id}); "
            "using forum_health.json for the group entity.",
            file=sys.stderr,
        )

    print("🔌 Connecting to Telegram (human session)...")
    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    async def get_code():
        return await otp_from_file(cfg.otp_code_file)

    await client.start(phone=cfg.phone, code_callback=get_code)
    full_group = await client.get_entity(fcfg.group_id)
    print(f"📍 Group: {getattr(full_group, 'title', fcfg.group_id)}")

    failures = 0
    for spec in fcfg.topics:
        label = spec.label
        bot = spec.bot_username
        tid = spec.topic_id
        print(f"\n── Topic {tid} ({label}) → @{bot} ──")
        try:
            top_mid = await get_topic_top_message_id(client, full_group, tid)
        except Exception as e:
            print(f"  ❌ could not resolve topic: {e}", file=sys.stderr)
            print(_debug_hint(label, bot), file=sys.stderr)
            failures += 1
            continue

        try:
            sent = await send_in_topic(client, full_group, fcfg.ping_message, top_mid)
        except FloodWaitError as e:
            print(f"  ⏳ FloodWait {e.seconds}s — sleeping", file=sys.stderr)
            await asyncio.sleep(e.seconds + 1)
            try:
                sent = await send_in_topic(client, full_group, fcfg.ping_message, top_mid)
            except Exception as e2:
                print(f"  ❌ send failed after flood wait: {e2}", file=sys.stderr)
                traceback.print_exc()
                failures += 1
                continue
        except Exception as e:
            print(f"  ❌ send failed: {e}", file=sys.stderr)
            traceback.print_exc()
            failures += 1
            continue

        try:
            reply = await wait_for_bot_reply_to_ping(
                client,
                full_group,
                bot,
                sent.id,
                topic_id=tid,
                top_message_id=top_mid,
                timeout=fcfg.reply_timeout_sec,
            )
        except Exception as e:
            print(f"  ❌ wait failed: {e}", file=sys.stderr)
            failures += 1
            continue

        if reply is not None:
            preview = (reply[:120] + "…") if len(reply) > 120 else reply
            print(f"  ✅ reply from @{bot}: {preview!r}")
        else:
            print(f"  ❌ no reply from @{bot} within {fcfg.reply_timeout_sec}s", file=sys.stderr)
            print(_debug_hint(label, bot), file=sys.stderr)
            failures += 1

    await client.disconnect()

    print()
    if failures:
        print(f"Forum health: FAILED ({failures} topic(s))", file=sys.stderr)
        return 1
    print("Forum health: OK")
    return 0


def main() -> None:
    sys.exit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
