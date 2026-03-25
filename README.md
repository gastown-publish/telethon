# gastown-publish/telethon

**Human-account (Telethon) integration tests** for Gastown Telegram bots powered by **Gasclaw** and **OpenClaw**.

This is **not** a Telegram bot library. It logs in as a **real user** via [Telethon](https://docs.telethon.dev/) so you can automate `@mentions`, `/subagents`, and health checks against `@gasclaw_master_bot`, `@minimax_gastown_publish_bot`, etc.

## Quick start

```bash
git clone https://github.com/gastown-publish/telethon.git
cd telethon
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

cp .env.example .env
# Edit .env: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_GROUP_ID, TELETHON_SESSION_PATH
```

Get `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org) (user API, not BotFather).

First-time login (SMS code):

```bash
gastown-telethon-ping
# When asked for OTP: echo 12345 > /tmp/tg_otp_code
```

Subsequent runs reuse `data/tg_session.session` (path from `TELETHON_SESSION_PATH`).

## Commands

| Entry point | Description |
|-------------|-------------|
| `gastown-telethon-ping` | Ping each bot in `TELEGRAM_TEST_PING_BOTS` with `@bot ping` |
| `gastown-telethon-integration` | Full scenario for gasclaw + minimax (spawn, lists, ignore rules) |
| `gastown-telethon-all-bots` | Every bot in `examples/bots.example.json` (override path with `TELETHON_BOTS_CONFIG`) |
| `gastown-telethon-forum-health` | **Per-topic forum health** — pings each bot in its topic ([examples/forum_health.example.json](examples/forum_health.example.json)); used by **gasclaw-management** monitoring |

Or run as modules:

```bash
python -m gastown_telethon.scripts.ping
python -m gastown_telethon.scripts.integration
python -m gastown_telethon.scripts.all_bots
```

## Environment variables

See [.env.example](.env.example). Required for all scripts:

- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- `TELEGRAM_GROUP_ID` — supergroup / forum id (negative integer)
- `TELETHON_SESSION_PATH` — base path for the session file (directory is created if needed)

Optional:

- `TELEGRAM_OTP_CODE_FILE` — default `/tmp/tg_otp_code`
- `TELETHON_FORUM_HEALTH_CONFIG` — path to JSON for `gastown-telethon-forum-health` (default: `examples/forum_health.example.json`). Per-topic **`"optional": true`** skips failure when a bot cannot reply (e.g. missing `botToken`).
- `TELEGRAM_TEST_GASCLAW_BOT`, `TELEGRAM_TEST_MINIMAX_BOT` — usernames for integration test
- `TELEGRAM_TEST_PING_BOTS` — comma-separated list for ping
- `TELETHON_BOTS_CONFIG` — JSON for `all_bots` (see [examples/bots.example.json](examples/bots.example.json))

## Running against Gasclaw

See [docs/gasclaw-integration.md](docs/gasclaw-integration.md) for how **OpenClaw + Gasclaw** (bot side) relates to this repo (human side), validation commands, and troubleshooting.

## Security

- Never commit `.env`, `*.session`, or API hashes.
- Treat `*.session` like a password (full account access).
- Rotate [my.telegram.org](https://my.telegram.org) credentials if exposed.
- If you previously committed `API_ID` / `API_HASH` / phone numbers in ad-hoc scripts under `telegram-test/`, rotate those credentials and rely on `.env` only.

## CI and pushing to GitHub

Nothing runs as a **daemon** by default: you execute scripts when you need them. Before every push, run:

```bash
./scripts/ci.sh
```

This runs:

1. **`scripts/scan_credentials.py`** — scans git-tracked files for Telegram bot-token shapes and 32-hex `api_hash` values (no `.env` or `*.session` should be committed).
2. **`pytest tests/`** — offline tests (no Telegram network or credentials).

GitHub Actions runs the same checks on every push and PR (`.github/workflows/ci.yml`).

**Optional local hook** (runs `ci.sh` before `git push`):

```bash
git config core.hooksPath .githooks
```

## Publishing this repository

The repo **already exists** at [github.com/gastown-publish/telethon](https://github.com/gastown-publish/telethon). To push from a fresh clone:

```bash
git clone https://github.com/gastown-publish/telethon.git
cd telethon
./scripts/ci.sh   # must pass before you push
git push
```

## License

MIT — see [LICENSE](LICENSE).
