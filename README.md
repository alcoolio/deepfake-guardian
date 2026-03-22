# Deepfake Guardian

Open-source content moderation system for **Telegram** and **WhatsApp** group chats.
Protects communities — especially those with minors — from violence, NSFW content,
sexual violence, and deepfakes in text, images, and videos.

> **Current state:** Phase 1 complete — tests, CI/CD, API key authentication, and
> retry/resilience are in place. Deepfake detection and video moderation are still
> stubs. No GDPR persistence yet.
> See [ROADMAP.md](ROADMAP.md) for the full development plan.

---

## Architecture

```
┌─────────────┐     HTTP/JSON     ┌──────────────────────┐
│ Telegram Bot │ ───────────────▶ │                      │
└─────────────┘                   │   Moderation Engine  │
                                  │      (FastAPI)        │
┌──────────────┐    HTTP/JSON     │                      │
│ WhatsApp Bot │ ───────────────▶ │  POST /moderate_text  │
└──────────────┘                   │  POST /moderate_image│
                                  │  POST /moderate_video │
                                  │  GET  /health         │
                                  └──────────────────────┘
```

| Directory | Stack | Purpose |
|-----------|-------|---------|
| `engine/` | Python 3.11, FastAPI | Content classification API |
| `telegram-bot/` | Python, python-telegram-bot | Telegram group listener |
| `whatsapp-bot/` | Node.js, TypeScript, Baileys | WhatsApp group listener |

---

## How It Works

1. A bot receives a message (text / image / video) in a group chat.
2. It forwards the content to the engine API.
3. The engine runs ML classifiers and returns a verdict:
   - `"allow"` — content is safe, no action
   - `"flag"` — scores are elevated, admins are notified
   - `"delete"` — content exceeds thresholds, message is deleted (if bot has admin rights) or admins are @-mentioned
4. The bot acts on the verdict.

### Moderation categories

| Category | Model | Status |
|----------|-------|--------|
| Violence | BART zero-shot (text) / CLIP zero-shot (image) | Working |
| Sexual violence | BART zero-shot (text) / CLIP zero-shot (image) | Working |
| NSFW | BART zero-shot (text) / CLIP zero-shot (image) | Working |
| Deepfake | — | **Stub** (fixed score 0.05) |
| Video | — | **Stub** (always "allow") |
| Cyberbullying | — | Planned (Phase 2) |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose, **or** Python 3.11+ and Node.js 18+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/deepfake-guardian.git
cd deepfake-guardian

cp engine/.env.example engine/.env
cp telegram-bot/.env.example telegram-bot/.env
cp whatsapp-bot/.env.example whatsapp-bot/.env
```

Edit `telegram-bot/.env` and set `TELEGRAM_BOT_TOKEN`.

### 2. Run with Docker Compose

```bash
docker compose up --build
```

The engine downloads ML models on first run (~1.5 GB). Subsequent starts use a
cached Docker volume.

### 3. Add the bot to a group

Invite the bot to a Telegram group and grant it **admin rights** so it can delete
messages. Without admin rights it will @-mention admins instead.

### 4. Run without Docker

```bash
# Terminal 1 — Engine
cd engine && pip install -r requirements.txt && python main.py

# Terminal 2 — Telegram bot
cd telegram-bot && pip install -r requirements.txt && python main.py

# Terminal 3 — WhatsApp bot
cd whatsapp-bot && npm install && npm run build && npm start
```

---

## Configuration

All services use `.env` files. See `.env.example` files for full lists.

### Engine thresholds (0–1 scale)

| Variable | Default | Meaning |
|----------|---------|---------|
| `THRESHOLD_VIOLENCE` | `0.7` | Delete threshold for violence |
| `THRESHOLD_SEXUAL_VIOLENCE` | `0.5` | Delete threshold for sexual violence |
| `THRESHOLD_NSFW` | `0.6` | Delete threshold for NSFW |
| `THRESHOLD_DEEPFAKE` | `0.8` | Delete threshold for deepfake |

Messages with any score **≥ 0.4** but below the delete threshold are **flagged** for
admin review instead of being deleted.

### Engine security

| Variable | Default | Meaning |
|----------|---------|---------|
| `API_KEY` | _(empty)_ | Secret key required in `X-API-Key` header; leave empty to disable auth (dev only) |
| `RATE_LIMIT` | `60/minute` | Max requests per IP per interval on moderation endpoints |

### Telegram bot

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Token from @BotFather |
| `ENGINE_URL` | No | Engine URL (default: `http://engine:8000`) |
| `ENGINE_API_KEY` | No | Must match `API_KEY` in `engine/.env` |

---

## Manual API Test

```bash
# Without authentication (API_KEY not set):
curl -s -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}' | python3 -m json.tool

# With authentication:
curl -s -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"text": "hello world"}' | python3 -m json.tool
```

Expected response:
```json
{
  "verdict": "allow",
  "reasons": [],
  "scores": {
    "violence": 0.02,
    "sexual_violence": 0.01,
    "nsfw": 0.01,
    "deepfake_suspect": 0.0
  }
}
```

---

## Running Tests

```bash
# Engine
cd engine && pip install -r requirements.txt && pytest

# Telegram bot
cd telegram-bot && pip install -r requirements.txt && pytest
```

---

## Known Limitations

- **Deepfake detection is a stub** — returns a fixed score of `0.05`. The pipeline
  is wired so a real model (e.g. EfficientNet on FaceForensics++) can be dropped in
  without changing the API. See `engine/classifiers.py`.
- **Video moderation is a stub** — always returns `"allow"`. Frame extraction is not
  yet implemented. See `engine/routes.py`.
- **English only** — i18n architecture with German as first language pack is Phase 2.
- **Stateless** — no database. GDPR-compliant audit logging is Phase 3.

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Tests, CI/CD, API auth, resilience | **Done** |
| 2 | i18n architecture, German + English language packs, cyberbullying | Planned |
| 3 | GDPR compliance, database, warning/escalation system | Planned |
| 4 | Real deepfake detection, video frame extraction | Planned |
| 5 | Admin dashboard, admin bot commands, educational feedback | Planned |
| 6 | WhatsApp parity, Signal & Discord bots, community language packs | Planned |

See [ROADMAP.md](ROADMAP.md) for the full plan including file-level details.

---

## Target Audiences

Deepfake Guardian is designed for organisations that run group chats with members
who need higher protection:

- **Schools and educational institutions** — student groups, class chats
- **Youth organisations** — scouts, sports clubs, youth centres
- **Companies and teams** — internal communication channels
- **Community groups** — hobby communities, local associations

The moderation strictness can be tuned per group profile
(planned in Phase 2: `minors_strict`, `minors_standard`, `default`, `permissive`).

---

## Security & Privacy

- Message content is **never stored** — only a short preview (80 chars) appears in
  structured logs for debugging.
- User IDs are not collected (stateless prototype).
- Phase 3 introduces GDPR-compliant audit logging: metadata only, hashed user IDs,
  automatic deletion after 30 days, right-to-erasure endpoint.
- GDPR compliance for minors is the strictest standard globally and covers COPPA
  (USA), PIPEDA (Canada), LGPD (Brazil), and similar frameworks.

---

## Contributing

Contributions are welcome. Please open an issue before starting large changes.

Areas where help is especially needed:
- Language packs (German is first priority, then French, Spanish, Turkish)
- A real deepfake detection model integration
- Tests
- Documentation translations

See [CLAUDE.md](CLAUDE.md) for a detailed technical orientation to the codebase.

---

## License

MIT — see [LICENSE](LICENSE).
