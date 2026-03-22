# Changelog

All notable changes to Deepfake Guardian are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

- `PATCH` bump (0.0.x) — docs, wording, renames, translations, minor fixes; nothing in the running system changes.
- `MINOR` bump (0.x.0) — new feature or capability added.
- `MAJOR` bump (x.0.0) — breaking change to API or behaviour.

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
- `ROADMAP.md` — translated from German to English; all section headings, descriptions,
  design principles, verification criteria, and commentary are now in English.

---

## [0.3.0] — 2026-03-22 — Phase 2: i18n Architecture, Cyberbullying & Language Packs

### Added

**Engine — i18n Architecture:**
- `engine/i18n/` package — language-agnostic moderation framework:
  - `engine/i18n/base.py` — abstract `LanguagePack` base class with `detect()`,
    `get_classifier()`, `get_labels()`, `get_patterns()`, `get_educational_messages()`,
    `get_helplines()` interface.  `HarmPattern` and `Helpline` dataclasses.
  - `engine/i18n/registry.py` — `LanguageRegistry` with auto-discovery: imports all
    modules in `engine/i18n/packs/` at startup and registers every `LanguagePack`
    subclass by its `lang_code`.  Adding a new language = one new file.
  - `engine/i18n/detector.py` — `detect_language(text)` iterates enabled packs,
    picks the highest-confidence match, falls back to `"en"`.
- `engine/i18n/packs/en.py` — **English language pack** (`EnglishPack`):
  - Migrates existing `facebook/bart-large-mnli` zero-shot classifier.
  - English cyberbullying patterns: death threats, targeted insults, exclusion
    language, extortion.
  - Helplines: Crisis Text Line, Cyberbullying Research Center, StopBullying.gov.
- `engine/i18n/packs/de.py` — **German language pack** (`GermanPack`):
  - Uses `ml6team/distilbert-base-german-cased-toxic-comments` (~260 MB, CPU-compatible).
  - German cyberbullying patterns: Todesdrohungen, Ausgrenzung, gezielte Beleidigungen,
    Erpressung, Doxxing indicators.
  - Helplines: Nummer gegen Kummer (116 111), Telefonseelsorge (0800 111 0 111),
    Jugendnotmail, Klicksafe.

**Engine — Cyberbullying Detection:**
- `engine/cyberbullying.py` — `score_cyberbullying(text, lang_pack)`: combines
  language-specific `HarmPattern` matches with cross-language structural patterns
  (pile-on @mentions, repeated insults, all-caps shouting).
- `ModerationScores` gains `cyberbullying: float` field (default `0.0` — fully
  backward compatible).
- `ModerationResult` gains `language: str | None` field (detected language code).
- `TextRequest` gains optional `language: str | None` hint to bypass auto-detection.
- New env var `THRESHOLD_CYBERBULLYING=0.6` (delete threshold for cyberbullying).
- `verdict.py` updated to check cyberbullying threshold and include `"cyberbullying"`
  / `"elevated_cyberbullying"` in reasons.

**Engine — Threshold Profiles:**
- `engine/profiles.py` — `ThresholdProfile` dataclass + three built-in profiles:
  - `minors_strict` (violence=0.5, sexual_violence=0.3, nsfw=0.4, deepfake=0.6, cyberbullying=0.4)
  - `default` (unchanged Phase 1 values + cyberbullying=0.6)
  - `permissive` (higher thresholds for adult communities)
- New env var `MODERATION_PROFILE=default` selects the active profile.  Individual
  `THRESHOLD_*` env vars still override individual profile values.
- `config.py` converted to `__init__`-based `Settings` to support profile-as-default
  pattern.

**Engine — Tests:**
- `engine/tests/test_i18n.py` — 18 tests covering registry discovery, pack interface,
  language detection with mocked `langdetect`.
- `engine/tests/test_cyberbullying.py` — 11 tests covering English and German patterns,
  structural patterns, graceful error handling.
- `engine/tests/test_verdict.py` — 3 new tests for cyberbullying threshold, flag path,
  and backward compatibility.
- `engine/tests/test_classifiers.py` — updated for new `classify_text` signature and
  return shape (includes `cyberbullying` and `lang_code` keys).

**Telegram Bot — i18n:**
- `telegram-bot/i18n/en.json` + `telegram-bot/i18n/de.json` — admin notification
  message templates in English and German.
- `telegram-bot/i18n/loader.py` — `get_message(key, lang, **kwargs)`: loads JSON
  templates, falls back to English, formats with `str.format_map`.
- `telegram-bot/main.py` — `_notify_admins()` now accepts a `language` parameter
  and uses `get_message()` to send localised notifications.  Language is taken from
  the engine's `ModerationResult.language` field (text moderation) or the
  `BOT_LANGUAGE` env var fallback (image/video moderation).

### Changed
- `engine/classifiers.py` — `classify_text()` refactored to route through the
  language registry; falls back to the legacy BART pipeline when no pack is found.
- `engine/config.py` — converted to `__init__`-based `Settings`; new fields:
  `enabled_languages`, `moderation_profile`, `threshold_cyberbullying`.
- `engine/.env.example` — added `ENABLED_LANGUAGES`, `MODERATION_PROFILE`,
  `THRESHOLD_CYBERBULLYING`.
- `engine/requirements.txt` — added `langdetect==1.0.9`.
- `telegram-bot/config.py` — added `bot_language` setting.
- `telegram-bot/.env.example` — added `BOT_LANGUAGE=en`.

---

## [0.2.0] — 2026-03-22 — Phase 1: Tests, CI/CD, API Auth, Resilience

### Added

**Engine — API Key Authentication & Rate Limiting:**
- `X-API-Key` middleware in `engine/main.py` — all moderation endpoints require a
  valid key when `API_KEY` env var is set; `/health` is always public.
- Per-IP rate limiting on `/moderate_text`, `/moderate_image`, `/moderate_video`
  via [slowapi](https://github.com/laurentS/slowapi) (default: `60/minute`,
  configurable via `RATE_LIMIT` env var).
- `API_KEY` and `RATE_LIMIT` added to `engine/config.py` and `engine/.env.example`.

**Engine — Test Suite:**
- `engine/tests/conftest.py` — shared pytest fixtures: `TestClient` with mocked
  ML classifiers (no GPU/download required), small test image helper.
- `engine/tests/test_verdict.py` — 12 unit tests covering allow/flag/delete
  threshold logic across all four score categories.
- `engine/tests/test_routes.py` — 16 integration tests for all four endpoints
  including API key authentication and error cases.
- `engine/tests/test_classifiers.py` — 12 unit tests for `decode_image`,
  `classify_text`, `classify_image`, and `detect_deepfake_suspect` with mocked
  pipelines.
- `engine/pyproject.toml` — pytest, ruff, and mypy configuration.

**Telegram Bot — Resilience & API Key:**
- `engine_client.py` rewritten with exponential-backoff retry logic: up to 3
  retries on network errors and 5xx responses (waits: 1s → 2s → 4s).
- `X-API-Key` header forwarded when `ENGINE_API_KEY` env var is set.
- `ENGINE_API_KEY` added to `telegram-bot/config.py` and `telegram-bot/.env.example`.
- `telegram-bot/tests/test_engine_client.py` — tests covering successful calls,
  retry on transport error, retry on 5xx, max-retry exhaustion, API key header.
- `telegram-bot/pyproject.toml` — pytest and ruff configuration.

**WhatsApp Bot — Resilience & API Key:**
- `src/engine-client.ts` rewritten with built-in retry loop (up to 3 retries,
  exponential backoff, retries on network errors and 5xx status codes).
- `X-API-Key` header forwarded when `ENGINE_API_KEY` env var is set.
- `ENGINE_API_KEY` added to `src/config.ts` and `whatsapp-bot/.env.example`.

**CI/CD — GitHub Actions:**
- `.github/workflows/ci.yml` — runs on every push/PR:
  - `engine` job: ruff lint, mypy type-check, pytest.
  - `telegram-bot` job: ruff lint, pytest.
  - `whatsapp-bot` job: TypeScript build (`tsc`).
- `.github/workflows/docker.yml` — builds all three Docker images on pushes/PRs
  to `master`/`main`.

### Changed
- `engine/requirements.txt` — added `slowapi==0.1.9`, `pytest==8.3.4`,
  `pytest-asyncio==0.24.0`.
- `telegram-bot/requirements.txt` — added `pytest==8.3.4`, `pytest-asyncio==0.24.0`.
- `engine/main.py` — version bumped to `0.2.0`; slowapi wired to app.
- `engine/routes.py` — all three POST handlers now accept `request: Request` as
  required by slowapi; shared `limiter` instance exported for `main.py`.
- `README.md` — updated status banner, added API auth/rate-limit config table,
  added "Running Tests" section, updated roadmap status.

---

## [0.0.3] — 2025-01-xx — Neutral Role Terminology in Roadmap

### Changed
- `ROADMAP.md` — replaced school-specific terminology with platform-neutral roles:
  Admin (group manager), Member (participant), Supervisor (higher-level oversight).
  Broadens the target audience beyond schools to any organisation running group chats.
  No behaviour change → patch bump.

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
