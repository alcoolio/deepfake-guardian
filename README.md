# Deepfake Guardian

Open-source content moderation system for **Telegram** and **WhatsApp** group chats.
Protects communities — especially those with minors — from violence, NSFW content,
sexual violence, cyberbullying, and deepfakes in text, images, and videos.

> **Current state:** Phase 3 complete — GDPR-compliant audit database, warning/escalation
> system, `/privacy` and `/delete_my_data` bot commands, and automatic data retention
> cleanup are all in place. Deepfake detection and video moderation are still stubs.
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
3. The engine detects the language, runs the appropriate ML classifier and
   pattern matcher, and returns a verdict:
   - `"allow"` — content is safe, no action
   - `"flag"` — scores are elevated, admins are notified
   - `"delete"` — content exceeds thresholds, message is deleted (if bot has admin rights) or admins are @-mentioned
4. The bot acts on the verdict and sends admin notifications in the detected language.

### Moderation categories

| Category | Model | Status |
|----------|-------|--------|
| Violence | BART zero-shot (EN) / German toxic model (DE) | ✅ Working |
| Sexual violence | BART zero-shot (EN) / German toxic model (DE) | ✅ Working |
| NSFW | BART zero-shot (EN) / German toxic model (DE) | ✅ Working |
| Cyberbullying | Language-specific patterns + ML labels | ✅ Working |
| Deepfake | — | **Stub** (fixed score 0.05) |
| Video | — | **Stub** (always "allow") |

---

## Language Packs

Deepfake Guardian uses a plugin architecture for language-aware moderation.
Each language pack lives in `engine/i18n/packs/<lang_code>.py` and is
auto-discovered at startup.

**Adding a new language** requires only one file:

```python
# engine/i18n/packs/fr.py
from i18n.base import HarmPattern, Helpline, LanguagePack

class FrenchPack(LanguagePack):
    lang_code = "fr"
    lang_name = "Français"

    def detect(self, text): ...
    def get_classifier(self): ...
    def get_labels(self): ...
    def get_patterns(self): ...
    def get_educational_messages(self): ...
    def get_helplines(self): ...
```

Enable it via `ENABLED_LANGUAGES=en,de,fr` in `engine/.env`.

**Currently bundled:**
- 🇬🇧 English (`en`) — `facebook/bart-large-mnli` zero-shot + EN patterns
- 🇩🇪 German (`de`) — `ml6team/distilbert-base-german-cased-toxic-comments` + DE patterns + Telefonseelsorge

---

## Quick Start

### Prerequisites

- Docker & Docker Compose, **or** Python 3.11+ and Node.js 18+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and configure

```bash
git clone https://github.com/alcoolio/deepfake-guardian.git
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

The engine downloads ML models on first run (~1.8 GB including the German model).
Subsequent starts use a cached Docker volume.

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

### Engine — i18n & language packs

| Variable | Default | Meaning |
|----------|---------|---------|
| `ENABLED_LANGUAGES` | `en,de` | Comma-separated list of active language pack codes |

### Engine — moderation profiles

| Variable | Default | Meaning |
|----------|---------|---------|
| `MODERATION_PROFILE` | `default` | Pre-configured threshold set: `minors_strict` \| `default` \| `permissive` |

Profiles set all thresholds at once. Individual `THRESHOLD_*` env vars override
specific values within the chosen profile.

| Profile | Violence | Sexual violence | NSFW | Deepfake | Cyberbullying |
|---------|----------|-----------------|------|----------|---------------|
| `minors_strict` | 0.5 | 0.3 | 0.4 | 0.6 | 0.4 |
| `default` | 0.7 | 0.5 | 0.6 | 0.8 | 0.6 |
| `permissive` | 0.85 | 0.7 | 0.75 | 0.9 | 0.8 |

### Engine — individual thresholds (0–1 scale)

| Variable | Default | Meaning |
|----------|---------|---------|
| `THRESHOLD_VIOLENCE` | `0.7` | Delete threshold for violence |
| `THRESHOLD_SEXUAL_VIOLENCE` | `0.7` | Delete threshold for sexual violence |
| `THRESHOLD_NSFW` | `0.6` | Delete threshold for NSFW |
| `THRESHOLD_DEEPFAKE` | `0.8` | Delete threshold for deepfake |
| `THRESHOLD_CYBERBULLYING` | `0.6` | Delete threshold for cyberbullying |

Messages with any score **≥ 0.4** but below the delete threshold are **flagged** for
admin review instead of being deleted.

### Engine — security

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
| `BOT_LANGUAGE` | No | Language for admin notifications: `en` or `de` (default: `en`) |

---

## Manual API Test

```bash
# Moderate English text
curl -s -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -d '{"text": "nobody likes you, you should die"}' | python3 -m json.tool

# Moderate German text
curl -s -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -d '{"text": "keiner mag dich, du solltest sterben"}' | python3 -m json.tool

# Explicit language hint
curl -s -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world", "language": "en"}' | python3 -m json.tool
```

Expected response shape:
```json
{
  "verdict": "allow",
  "reasons": [],
  "scores": {
    "violence": 0.02,
    "sexual_violence": 0.01,
    "nsfw": 0.01,
    "deepfake_suspect": 0.0,
    "cyberbullying": 0.01
  },
  "language": "en"
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
- **Stateless** — no database. GDPR-compliant audit logging is Phase 3.

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Tests, CI/CD, API auth, resilience | ✅ Done |
| 2 | i18n architecture, German + English language packs, cyberbullying | ✅ Done |
| 3 | GDPR compliance, database, warning/escalation system | ✅ Done |
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

Use `MODERATION_PROFILE=minors_strict` for groups with minors.

---

## GDPR & Privacy

### What is stored

| Data | Stored? | Notes |
|------|---------|-------|
| Message text / images / video | **Never** | Processed in memory only |
| Moderation verdict + scores | ✅ (metadata only) | Deleted after `DATA_RETENTION_DAYS` (default 30) |
| User/group identifiers | ✅ (hashed) | SHA-256 with secret salt — not reversible |
| Warning counts | ✅ | Deleted on erasure request |

### Engine — GDPR configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./deepfake_guardian.db` | SQLite (default) or PostgreSQL asyncpg URL |
| `GDPR_SALT` | *(change me)* | Secret salt for SHA-256 hashing — **set a strong random value in production** |
| `DATA_RETENTION_DAYS` | `30` | Days before moderation events are auto-deleted |

### User rights (GDPR Articles 15–17)

| Command | Behaviour |
|---------|-----------|
| `/privacy` | Shows the full privacy notice in the group |
| `/delete_my_data` | Submits an Article 17 erasure request; all stored data is deleted within 30 days |

Engine API endpoints for programmatic access:

```
POST /gdpr/export                  — Article 15: export all data for a user
POST /gdpr/delete_request          — Article 17: submit erasure request
GET  /gdpr/delete_request/{id}     — check erasure request status
```

### Warning / escalation system

```
POST /warnings/record              — record a violation, returns escalation action
GET  /warnings/{user_id_hash}      — fetch warning history for a user
```

Escalation levels per (user, group):

| Violation count | Action |
|----------------|--------|
| 1st | `notice` — educational reply in the group |
| 2nd | `admin_notification` — @-mention group admins |
| 3rd+ | `supervisor_escalation` — urgent admin mention with incident count |

### Security & Privacy notes

- Message content is **never stored** — only a 80-char preview appears in
  structured debug logs (never in the database).
- User IDs are hashed with SHA-256 + secret salt before storage.
- GDPR compliance for minors is the strictest standard globally and covers
  COPPA (USA), PIPEDA (Canada), LGPD (Brazil), and similar frameworks.
- See `engine/privacy_policy.md` for a deployable privacy policy template.

---

## Contributing

Contributions are welcome. Please open an issue before starting large changes.

Areas where help is especially needed:
- Language packs (French, Spanish, Turkish, Arabic are next priorities)
- A real deepfake detection model integration
- Tests
- Documentation translations

See [CLAUDE.md](CLAUDE.md) for a detailed technical orientation to the codebase.

---

## License

MIT — see [LICENSE](LICENSE).
