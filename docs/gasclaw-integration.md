# Running Gasclaw with this Telethon test harness

This repository tests **Telegram bots** that are driven by **OpenClaw inside Gasclaw**. The bots are **not** part of this repo; this repo only provides a **human Telethon session** to send messages and observe replies.

## Architecture

```
┌─────────────────┐     MTProto (user)      ┌──────────────────────────┐
│  Telethon       │  ───────────────────►   │  Telegram servers        │
│  (this repo)    │  ◄───────────────────   │                          │
└─────────────────┘                         └────────────┬─────────────┘
                                                         │
┌─────────────────┐     Bot API                 ┌────────▼─────────────┐
│  OpenClaw       │  ◄────────────────────────► │  Same group / forum  │
│  (Gasclaw       │                             │  (gastown_publish)    │
│   container)    │                             └──────────────────────┘
└─────────────────┘
```

1. **Gasclaw** reads `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`, `TELEGRAM_GROUP_IDS`, etc., and writes `~/.openclaw/openclaw.json` during bootstrap.
2. **OpenClaw gateway** must be running (`openclaw gateway run` or your container entrypoint).
3. **This repo** uses your **personal Telegram account** via Telethon to `@mention` bots and run `/subagents` tests.

## Prerequisites

- A **Gasclaw** (or OpenClaw-only) deployment with Telegram enabled and the bot(s) added to the target group/forum.
- Your human user account is a **member** of that group (and has access to the forum topic if applicable).
- **Telegram Privacy Mode**: for group tests, the bot usually must see messages when mentioned; see Gasclaw’s `openclaw-telegram.md` (Privacy Mode / admin).

## Configure Gasclaw (bot side)

On the Gasclaw host or inside the container, set at least:

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_OWNER_ID` | Your numeric user id |
| `TELEGRAM_GROUP_IDS` | Colon-separated supergroup ids (negative) |

Then validate:

```bash
openclaw config validate
openclaw channels status --probe
```

### Forum topic isolation (one bot per topic)

In a **forum** supergroup, each Gasclaw/OpenClaw deployment should answer **only in its dedicated topic**. In `openclaw.json`, under `channels.telegram.groups.<group_id>.topics`, configure each numeric topic id:

- **This bot’s topic:** leave enabled (default), set `requireMention` to `false` if you want replies without `@mention` inside that topic.
- **Other topics:** set `enabled: false` so this bot does not handle messages there.

That way each agent stays scoped to its thread; users organize work by topic.

The **`gastown-telethon-forum-health`** command pings each topic in order and accepts a reply only from the configured bot **in the same forum thread** as that ping (see `gastown_telethon/forum.py`). It does **not** treat unrelated group traffic as success.

Canonical references (paths vary by machine):

- `gasclaw/docs/guides/openclaw-telegram.md`
- `gasclaw/reference/openclaw-telegram.md`
- `gasclaw-management/docs/openclaw-config.md`

## Configure this repo (human side)

1. Clone [gastown-publish/telethon](https://github.com/gastown-publish/telethon).
2. `cd telethon && python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -e .`
4. Copy `.env.example` to `.env` and set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `TELEGRAM_GROUP_ID`, `TELETHON_SESSION_PATH`.
5. First login: run `gastown-telethon-ping` or any script; when prompted for OTP, write digits to `TELEGRAM_OTP_CODE_FILE` (default `/tmp/tg_otp_code`), e.g. `echo 12345 > /tmp/tg_otp_code`.
6. Reuse the same `TELETHON_SESSION_PATH` on later runs (no OTP).

## What to run against a live Gasclaw

| Command | Use |
|---------|-----|
| `gastown-telethon-ping` | Fast health: each bot gets `@bot ping` |
| `gastown-telethon-integration` | Deep test: two bots, spawn, `/subagents`, ignore-unmentioned |
| `gastown-telethon-all-bots` | Uses `examples/bots.example.json` (override with `TELETHON_BOTS_CONFIG`) |

Exit code `0` means all checks passed.

## Same machine vs different machine

- **Same machine as Gasclaw**: point `TELETHON_SESSION_PATH` at a directory your user owns (e.g. `./data/tg_session`). No link to Gasclaw’s `.env` is required; human credentials are separate.
- **CI / runner**: store the `.session` file as a protected secret artifact or use a dedicated test account and session vault—never commit `*.session`.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No reply from bot | Gateway running? `openclaw channels status --probe`. Bot in group? Correct `group_id`? |
| Bot only sometimes sees messages | Privacy Mode / mention rules in `openclaw.json` `groups` / `requireMention` |
| Telethon login fails | `api_id` / `api_hash` from my.telegram.org; phone in international format |
| Tests flaky | Increase sleeps or timeouts; forum topics may delay delivery |
