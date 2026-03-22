# Changelog

All notable changes to Deepfake Guardian are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project does not yet use semantic versioning — entries are grouped by git
milestone until the first stable release.

---

## [Unreleased]

### Added
- `CLAUDE.md` — full technical orientation for Claude and contributors: architecture,
  file-level descriptions, current limitations, roadmap summary, env variable reference,
  code conventions, and security notes.
- `CHANGELOG.md` — this file.

### Changed
- `README.md` — rewritten in English as the primary repository language; added
  moderation category status table, known limitations section, target audience
  section, contributing guidance, and security & privacy notes.

---

## [0.3.0] — 2025-01-xx — Neutral Role Terminology in Roadmap

### Changed
- `ROADMAP.md` — replaced school-specific terminology with platform-neutral roles:
  Admin (group manager), Member (participant), Supervisor (higher-level oversight).
  Broadens the target audience beyond schools to any organisation running group chats.

---

## [0.2.0] — 2025-01-xx — Development Roadmap

### Added
- `ROADMAP.md` — six-phase development plan covering:
  - Phase 1: Tests, CI/CD, API auth, error handling
  - Phase 2: i18n architecture, cyberbullying detection, German + English language packs
  - Phase 3: GDPR compliance, database, warning/escalation system
  - Phase 4: Real deepfake model, video frame extraction
  - Phase 5: Admin dashboard, admin bot commands, educational feedback
  - Phase 6: WhatsApp parity, Signal/Discord bots, community language packs
- i18n architecture design: `LanguagePack` abstract base class, plugin registry,
  language detector/router. Adding a new language = one Python file.
- Internationalisation strategy as competitive differentiator (vs. English-only tools).

---

## [0.1.0] — 2025-01-xx — Initial Prototype

### Added

**Engine (`engine/`)** — FastAPI content classification service:
- `POST /moderate_text` — classifies plain text using `facebook/bart-large-mnli`
  zero-shot classifier; categories: violence, sexual_violence, nsfw.
- `POST /moderate_image` — classifies images using CLIP zero-shot; also calls
  deepfake stub.
- `POST /moderate_video` — stub endpoint (always returns `"allow"`); wired and
  ready for real frame extraction.
- `GET /health` — liveness check.
- `verdict.py` — threshold-based decision engine: scores → `"allow"` / `"flag"` /
  `"delete"`.
- `models.py` — Pydantic v2 schemas (`ModerationResult`, `ModerationScores`,
  `TextRequest`, `ImageRequest`, `VideoRequest`).
- `config.py` — all configuration from env vars with defaults
  (`THRESHOLD_VIOLENCE=0.7`, `THRESHOLD_SEXUAL_VIOLENCE=0.5`, `THRESHOLD_NSFW=0.6`,
  `THRESHOLD_DEEPFAKE=0.8`).
- Structured logging via `structlog`.
- `Dockerfile` + `.env.example`.

**Telegram Bot (`telegram-bot/`)** — python-telegram-bot group listener:
- Handles text messages, photos, and videos in group chats (ignores private chats
  and commands).
- `engine_client.py` — async HTTP client for the engine API.
- Verdict actions: delete message (if bot is admin) or @-mention group admins.
- Structured logging via `structlog`.
- `Dockerfile` + `.env.example`.

**WhatsApp Bot (`whatsapp-bot/`)** — TypeScript/Node.js bot using Baileys:
- Mirrors Telegram bot behaviour for WhatsApp groups.
- `Dockerfile` + `.env.example`.

**Infrastructure:**
- `docker-compose.yml` — orchestrates all three services; ML model cache via
  Docker volume.
- `LICENSE` (MIT).

### Known limitations at this stage
- Deepfake detection is a **stub** — `detect_deepfake_suspect()` always returns `0.05`.
- Video moderation is a **stub** — `moderate_video` always returns `"allow"`.
- Image violence score always returns `0.0`.
- No tests, no CI/CD.
- No API authentication on the engine.
- No database or GDPR features.
- English-only; i18n not yet implemented.
- No cyberbullying detection.

---

[Unreleased]: https://github.com/alcoolio/deepfake-guardian/compare/HEAD...HEAD
