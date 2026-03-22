# Deepfake Guardian — Entwicklungsplan

## Kontext

Das Monorepo enthält drei Services (engine, telegram-bot, whatsapp-bot) als funktionsfähigen Prototyp. Primäre Zielgruppe: **Chatgruppen mit Minderjährigen** (z.B. Schulen, Jugendorganisationen, Sportvereine). Weitere Zielgruppen: Community-Gruppen, Organisationen, Unternehmen. Der aktuelle Stand hat kritische Lücken: keine Tests, kein DSGVO-Konzept, Deepfake-Erkennung ist ein Stub, keine deutsche Sprachunterstützung, keine Cybermobbing-Erkennung, kein Dashboard.

**Rollen-Terminologie (neutral, nicht schulspezifisch):**
- **Admin** = Gruppenverantwortliche (Lehrkräfte, Trainer, Moderatoren, etc.)
- **Member** = Gruppenmitglieder (Schüler:innen, Teilnehmer:innen, etc.)
- **Supervisor** = Übergeordnete Aufsicht (Schulleitung, Vereinsvorstand, etc.)

**Entscheidungen des Users:**
- Telegram hat höhere Priorität (offizielle API, einfacher)
- Einfaches Web-Dashboard für Admins
- Volle DSGVO-Compliance (Minderjährige = höchste Schutzstufe)

---

## Phase 1: Foundation & Produktionsreife

**Ziel:** Den bestehenden Code testbar, sicher und deploybar machen.

### 1.1 Tests & Linting
- **Neue Dateien:**
  - `engine/tests/test_routes.py` — Pytest-Tests für alle 3 Endpunkte + /health
  - `engine/tests/test_verdict.py` — Unit-Tests für Schwellwert-Logik
  - `engine/tests/test_classifiers.py` — Tests mit gemockten Pipelines
  - `engine/tests/conftest.py` — Fixtures (FastAPI TestClient, Mock-Bilder)
  - `telegram-bot/tests/test_handlers.py` — Tests mit gemocktem Engine-Client
  - `engine/pyproject.toml` — pytest, black, ruff, mypy Konfiguration
- **Modifizierte Dateien:**
  - `engine/requirements.txt` — pytest, httpx[test], pytest-asyncio hinzufügen
  - `telegram-bot/requirements.txt` — pytest hinzufügen

### 1.2 CI/CD Pipeline
- **Neue Dateien:**
  - `.github/workflows/ci.yml` — Lint + Test + Type-Check für engine & telegram-bot
  - `.github/workflows/docker.yml` — Docker-Build-Validierung

### 1.3 Engine-API absichern
- **Modifizierte Dateien:**
  - `engine/config.py` — `API_KEY` aus .env laden
  - `engine/main.py` — FastAPI Middleware für API-Key-Validierung + Rate Limiting
  - `engine/requirements.txt` — `slowapi` für Rate Limiting
  - `engine/.env.example` — `API_KEY` Feld hinzufügen
  - `telegram-bot/engine_client.py` — API-Key Header mitsenden
  - `telegram-bot/.env.example` — `ENGINE_API_KEY` Feld
  - `whatsapp-bot/src/engine-client.ts` — API-Key Header
  - `whatsapp-bot/.env.example` — `ENGINE_API_KEY` Feld

### 1.4 Fehlerbehandlung & Resilienz
- **Modifizierte Dateien:**
  - `telegram-bot/engine_client.py` — Retry-Logik mit exponentiellem Backoff (tenacity)
  - `telegram-bot/main.py` — Graceful Handling wenn Engine nicht erreichbar
  - `whatsapp-bot/src/engine-client.ts` — axios-retry hinzufügen

**Aufwand:** M | **Ergebnis:** Testbarer, abgesicherter Prototyp mit CI/CD

---

## Phase 2: i18n-Architektur, Cybermobbing-Erkennung & Sprachpakete

**Ziel:** Eine sprachunabhängige Moderations-Architektur aufbauen. Deutsch als erstes Sprachpaket implementieren. Jede weitere Sprache + kulturspezifische Regeln sollen ohne Code-Änderungen nachrüstbar sein.

### 2.1 i18n-Kern-Architektur (Engine)
- **Neue Dateien:**
  - `engine/i18n/` — i18n-Framework:
    - `engine/i18n/__init__.py` — Sprach-Registry, Auto-Discovery von Sprachpaketen
    - `engine/i18n/base.py` — Abstrakte Basisklasse `LanguagePack`:
      - `detect(text) -> float` — Konfidenz, dass Text dieser Sprache ist
      - `get_classifier() -> TextClassifier` — Sprachspezifisches ML-Modell
      - `get_patterns() -> list[HarmPattern]` — Regex/Keyword-basierte Patterns
      - `get_labels() -> dict[str, str]` — Lokalisierte Kategorie-Namen
      - `get_educational_messages() -> dict[str, str]` — Educational Feedback Texte
      - `get_helplines() -> list[Helpline]` — Lokale Hilfs- und Beratungsangebote
    - `engine/i18n/registry.py` — Plugin-Registry: Lädt alle `LanguagePack`-Subklassen automatisch
    - `engine/i18n/detector.py` — Sprach-Router: Erkennt Sprache → wählt passendes Pack
  - `engine/i18n/packs/` — Sprachpaket-Verzeichnis:
    - `engine/i18n/packs/__init__.py`
    - `engine/i18n/packs/de.py` — **Deutsches Sprachpaket** (erste Implementierung, s. 2.2)
    - `engine/i18n/packs/en.py` — **Englisches Sprachpaket** (migriert bestehenden BART-Classifier)

- **Design-Prinzipien:**
  - Jedes Sprachpaket ist ein einzelnes Python-Modul in `engine/i18n/packs/`
  - Neues Paket = neue Datei + Klasse die `LanguagePack` erbt → fertig
  - Kein Code in engine/classifiers.py oder routes.py muss geändert werden
  - Sprachpakete können per Config aktiviert/deaktiviert werden
  - Community kann Pakete als separate Repos entwickeln (future: pip-installierbar)

- **Modifizierte Dateien:**
  - `engine/classifiers.py` — `classify_text()` refactored: ruft i18n-Router auf
  - `engine/config.py` — `ENABLED_LANGUAGES=de,en` (kommasepariert)
  - `engine/requirements.txt` — `langdetect` oder `lingua-language-detector` hinzufügen

### 2.2 Deutsches Sprachpaket (erstes `LanguagePack`)
- **Datei:** `engine/i18n/packs/de.py`
  - **ML-Modell:** `ml6team/distilbert-base-german-cased-toxic-comments` oder vergleichbar (CPU-tauglich, ~260MB)
  - **Kategorien:** Beleidigung, Bedrohung, sexualisierte Sprache, Hate Speech, Cybermobbing
  - **Kulturspezifische Patterns (Regex/Keywords):**
    - Deutsche Schimpfwörter und Jugendsprache
    - Ausgrenzungs-Sprache ("du gehörst nicht dazu", "keiner mag dich")
    - Erpressungs-Muster ("ich zeig das allen", "wenn du nicht...")
    - Doxxing-Indikatoren (deutsche Adressformate, Telefonnummern)
  - **Educational Messages:** Erklärungen auf Deutsch (altersgerecht konfigurierbar)
  - **Support Resources:** Nummer gegen Kummer, Jugendnotmail, Telefonseelsorge, etc.

### 2.3 Englisches Sprachpaket (Migration)
- **Datei:** `engine/i18n/packs/en.py`
  - Migriert bestehenden `facebook/bart-large-mnli` Zero-Shot-Classifier
  - Englische Patterns und Hilfsangebote
  - Stellt sicher: bestehende Funktionalität bleibt intakt

### 2.4 Cybermobbing als Moderations-Kategorie
- **Neue Dateien:**
  - `engine/cyberbullying.py` — Sprachübergreifender Cybermobbing-Detector:
    - Strukturelle Muster (nicht sprachgebunden): z.B. @mention + negative Emotion
    - Wiederholungsmuster: gleicher User → gleiches Ziel mehrfach
    - Kontext-Analyse: Gruppen-Dynamik (wird eine Person immer angegriffen?)
    - Nutzt sprachspezifische Patterns aus dem jeweiligen `LanguagePack`
- **Modifizierte Dateien:**
  - `engine/models.py` — `ModerationScores` um `cyberbullying: float` erweitern
  - `engine/verdict.py` — Cyberbullying-Schwellwert einbauen
  - `engine/config.py` — `THRESHOLD_CYBERBULLYING=0.5`

### 2.5 Schwellwert-Profile
- **Neue Dateien:**
  - `engine/profiles.py` — Vordefinierte Threshold-Sets:
    - `minors_strict` (niedrigere Schwellwerte, strengere Moderation — für Gruppen mit Minderjährigen)
    - `minors_standard` (Standard für Gruppen mit Minderjährigen)
    - `default` (aktuelle Werte, für allgemeine Gruppen)
    - `permissive` (höhere Schwellwerte, weniger Eingriffe — für erwachsene Communities)
    - Profile sind JSON-serialisierbar → können später per Dashboard konfiguriert werden
- **Modifizierte Dateien:**
  - `engine/config.py` — `MODERATION_PROFILE=default`
  - `engine/verdict.py` — Profil-basierte Schwellwerte nutzen

### 2.6 Bot-Nachrichten i18n
- **Neue Dateien:**
  - `telegram-bot/i18n/` — Bot-UI-Texte (getrennt von Engine-i18n):
    - `telegram-bot/i18n/de.json` — Deutsche Bot-Nachrichten ("Nachricht wurde entfernt weil...")
    - `telegram-bot/i18n/en.json` — Englische Bot-Nachrichten
  - `telegram-bot/i18n/loader.py` — Lädt JSON, Fallback auf Englisch
- **Modifizierte Dateien:**
  - `telegram-bot/main.py` — Alle hardcodierten Strings durch i18n-Lookups ersetzen
  - `telegram-bot/config.py` — `BOT_LANGUAGE=de` Einstellung

**Aufwand:** L-XL | **Ergebnis:** Sprachunabhängige Architektur mit Deutsch + Englisch. Neue Sprachen = neue Datei in `packs/`. Bot-UI lokalisiert.

> **Warum das ein Wettbewerbsvorteil ist:** Die meisten Content-Moderation-Tools sind English-only. Eine i18n-first Architektur + DSGVO-Compliance macht Deepfake Guardian attraktiv für Organisationen weltweit — nicht nur DACH.

---

## Phase 3: DSGVO-Compliance & Persistenz

**Ziel:** Volle DSGVO-Konformität für Minderjährigendaten. Audit-Logging mit automatischen Löschfristen.

### 3.1 Datenbank-Setup
- **Neue Dateien:**
  - `engine/database.py` — SQLAlchemy-Setup (SQLite default, PostgreSQL optional)
  - `engine/db_models.py` — ORM-Modelle:
    - `ModerationEvent`: timestamp, group_id (gehasht), verdict, reasons, scores, content_type (kein Nachrichteninhalt!)
    - `UserWarning`: user_id_hash, group_id_hash, warning_count, last_warning, reason
    - `ConsentRecord`: user_id_hash, consent_given, consent_date, consent_scope
    - `DeletionRequest`: requester_hash, request_date, status, completed_date
  - `engine/alembic/` — Datenbank-Migrationen
- **Modifizierte Dateien:**
  - `engine/requirements.txt` — sqlalchemy, alembic, aiosqlite hinzufügen
  - `engine/routes.py` — ModerationEvents loggen nach jeder Entscheidung
  - `docker-compose.yml` — Volume für SQLite-Datenbank

### 3.2 DSGVO-Kernfunktionen
- **Neue Dateien:**
  - `engine/gdpr.py` — DSGVO-Service:
    - Automatische Löschung nach konfigurierbarer Frist (Standard: 30 Tage)
    - Auskunftsrecht: API-Endpoint `/gdpr/data_export/{user_hash}`
    - Löschrecht: API-Endpoint `/gdpr/delete_request`
    - Alle User-IDs werden vor Speicherung gehasht (SHA-256 + Salt)
    - Kein Nachrichteninhalt wird gespeichert — nur Metadaten + Scores
  - `engine/privacy_policy.md` — Datenschutzerklärung (Template)
- **Modifizierte Dateien:**
  - `engine/routes.py` — GDPR-Router einbinden
  - `engine/config.py` — `DATA_RETENTION_DAYS=30`, `GDPR_SALT` (Secret)
  - `engine/.env.example` — GDPR-Konfiguration

### 3.3 Einwilligungsmanagement
- **Modifizierte Dateien:**
  - `telegram-bot/main.py` — Bei erstem Kontakt: Datenschutzhinweis senden, Einwilligung abfragen
  - `telegram-bot/main.py` — `/privacy` Befehl: zeigt Datenschutzinfos
  - `telegram-bot/main.py` — `/delete_my_data` Befehl: Löschantrag stellen

### 3.4 Warn-/Eskalationssystem
- **Neue Dateien:**
  - `engine/warnings.py` — Warn-Service:
    - 1. Verstoß: Pädagogischer Hinweis (DM an User)
    - 2. Verstoß: Warnung + Admin-Benachrichtigung
    - 3. Verstoß: Automatische Meldung an Supervisor (konfigurierbar)
    - Zähler pro Member+Gruppe, konfigurierbare Eskalationsstufen
- **Modifizierte Dateien:**
  - `engine/routes.py` — `/warnings/{user_hash}` Endpoints
  - `telegram-bot/main.py` — Warn-Logik in `_handle_verdict()` integrieren

**Aufwand:** XL | **Ergebnis:** DSGVO-konforme Moderation mit Audit-Trail und konfigurierbarem Eskalationssystem

---

## Phase 4: Deepfake-Erkennung & Video-Analyse

**Ziel:** Den Deepfake-Stub durch ein echtes Modell ersetzen. Video-Frame-Extraktion implementieren.

### 4.1 Deepfake-Modell Integration
- **Modifizierte Dateien:**
  - `engine/classifiers.py` — `detect_deepfake_suspect()` ersetzen:
    - Modell: EfficientNet-B0 fine-tuned auf FaceForensics++ (ONNX-Format, ~20MB, CPU-tauglich)
    - Vorverarbeitung: Gesichtserkennung via `mediapipe` oder `retinaface` (leichtgewichtig)
    - Pipeline: Bild → Gesichter extrahieren → pro Gesicht Deepfake-Score → Aggregation
  - `engine/requirements.txt` — onnxruntime, mediapipe hinzufügen

### 4.2 Video-Frame-Extraktion
- **Neue Dateien:**
  - `engine/video_processing.py` — Frame-Extraktion:
    - OpenCV-basiert: Key-Frames alle N Sekunden extrahieren
    - Szenen-Erkennung: Frames bei Szenenwechsel
    - Max-Frame-Limit (z.B. 10 Frames pro Video) für Performance
    - Aggregation: Höchster Score über alle Frames
- **Modifizierte Dateien:**
  - `engine/routes.py` — `/moderate_video` mit echtem Frame-Processing
  - `engine/requirements.txt` — opencv-python-headless hinzufügen
  - `engine/Dockerfile` — ffmpeg installieren

### 4.3 Bild-Gewalt-Erkennung
- **Modifizierte Dateien:**
  - `engine/classifiers.py` — `classify_image()` erweitern:
    - Zusätzliches Modell für Gewalt-Erkennung in Bildern
    - Aktuell gibt `violence` immer 0.0 zurück — das beheben

**Aufwand:** L | **Ergebnis:** Echte Deepfake-Erkennung + funktionierende Video-Moderation

---

## Phase 5: Admin-Dashboard & Moderations-Tools

**Ziel:** Einfaches Web-Dashboard für Admins: Überblick über Moderation, Statistiken, Konfiguration.

### 5.1 Dashboard-Backend (Engine erweitern)
- **Neue Dateien:**
  - `engine/dashboard_routes.py` — API-Endpunkte:
    - `GET /dashboard/stats` — Moderations-Statistiken (letzte 7/30 Tage)
    - `GET /dashboard/events` — Paginierte Event-Liste (gefiltert nach Gruppe, Zeitraum, Verdict)
    - `GET /dashboard/warnings` — Aktive Warnungen
    - `POST /dashboard/config` — Gruppen-Konfiguration ändern
    - `GET /dashboard/digest` — Wöchentlicher Zusammenfassungsbericht
  - `engine/auth.py` — Dashboard-Authentifizierung (JWT-basiert, Login via Token)

### 5.2 Dashboard-Frontend
- **Neue Dateien:**
  - `dashboard/` — Neues Verzeichnis im Monorepo:
    - React (Vite) mit TypeScript
    - Minimales UI: Tailwind CSS
    - Seiten: Login, Übersicht, Events, Warnungen, Konfiguration
    - Diagramme: Moderations-Events über Zeit (Chart.js oder recharts)
  - `dashboard/Dockerfile` — Nginx serving static build
- **Modifizierte Dateien:**
  - `docker-compose.yml` — Dashboard-Service hinzufügen (Port 3000)

### 5.3 Bot-Befehle für Admins
- **Modifizierte Dateien:**
  - `telegram-bot/main.py` — Admin-Befehle:
    - `/stats` — Kurzstatistik der letzten 7 Tage
    - `/config` — Aktuelle Schwellwerte anzeigen/ändern
    - `/warnings @user` — Warnhistorie eines Users
    - `/digest` — Wöchentlichen Report anfordern
    - `/help_mod` — Hilfe zu allen Moderations-Befehlen

### 5.4 Pädagogische Feedback-Nachrichten
- Nutzt die `get_educational_messages()` und `get_helplines()` aus den LanguagePacks (Phase 2)
- Keine neue Datei nötig — die i18n-Architektur liefert die Inhalte bereits sprachspezifisch
- **Modifizierte Dateien:**
  - `telegram-bot/main.py` — Bei Warn/Delete: Educational Feedback DM an Member senden (Sprache = Gruppen-Sprache)

**Aufwand:** XL | **Ergebnis:** Admins haben ein Dashboard + Bot-Befehle + Members erhalten Educational Feedback in ihrer Sprache

---

## Phase 6: Skalierung & Ökosystem

**Ziel:** Weitere Messenger, Skalierung, Plugin-System.

### 6.1 WhatsApp-Bot vervollständigen
- Paritätische Funktionen zum Telegram-Bot (Warn-System, Befehle, DSGVO)
- Alle Features aus Phase 2-5 portieren

### 6.2 Weitere Plattformen
- **Neue Verzeichnisse:**
  - `signal-bot/` — Signal-Messenger Bot (signal-cli oder libsignal)
  - `discord-bot/` — Discord Bot (discord.js) — relevant für Gaming-Communities und Jugendgruppen

### 6.3 Kubernetes & Skalierung
- **Neue Dateien:**
  - `k8s/` — Kubernetes Manifeste (Deployment, Service, Ingress, PVC)
  - `engine/Dockerfile.gpu` — GPU-optimiertes Image für größere Installationen

### 6.4 Plugin-System & Community-Sprachpakete
- Engine-Plugins für benutzerdefinierte Classifier (Organisationen können eigene Regeln hinzufügen)
- `pip install deepfake-guardian-lang-fr` → Französisches Sprachpaket als separates Paket
- Community-Beiträge: Sprachpakete als eigene Repos mit standardisiertem Interface (LanguagePack)
- Dokumentation: "How to create a Language Pack" Guide

### 6.5 Weitere Sprachpakete (Community-driven)
- Priorisierte Sprachen basierend auf Nachfrage:
  - `fr` — Französisch (Frankreich, Belgien, Schweiz, Kanada)
  - `es` — Spanisch (Spanien, Lateinamerika)
  - `tr` — Türkisch (große Diaspora in DACH)
  - `ar` — Arabisch (wachsende Nachfrage)
  - `it` — Italienisch (Schweiz, Italien)
- Jedes Paket bringt mit: ML-Modell, kulturspezifische Patterns, Support Resources, Educational Messages

**Aufwand:** XL | **Ergebnis:** Multi-Plattform, multilingual, skalierbar, erweiterbar

---

## Zusammenfassung Reihenfolge

| Phase | Fokus | Aufwand | Abhängigkeit |
|-------|-------|---------|--------------|
| 1 | Tests, CI/CD, API-Auth, Resilienz | M | — |
| 2 | i18n-Architektur, Cybermobbing, DE+EN Sprachpakete | L-XL | Phase 1 |
| 3 | DSGVO, Datenbank, Warnsystem, Einwilligung | XL | Phase 1 |
| 4 | Echte Deepfake-Erkennung, Video-Analyse | L | Phase 1 |
| 5 | Dashboard, Admin-Tools, Feedback | XL | Phase 2+3 |
| 6 | WhatsApp-Parität, Signal, Discord, Community-Sprachen | XL | Phase 5 |

Phase 2, 3 und 4 können **teilweise parallel** entwickelt werden (unabhängige Codepfade). Phase 5 benötigt die Datenbank aus Phase 3 und die i18n-Architektur aus Phase 2.

---

## Verifizierung pro Phase

- **Phase 1:** `pytest` läuft grün, CI-Pipeline grün, Engine lehnt Requests ohne API-Key ab
- **Phase 2:** `engine/i18n/packs/de.py` erkennt "Du bist so hässlich" als Cybermobbing. Neues Sprachpaket = 1 neue Datei. Bot antwortet auf Deutsch. `minors_strict` Profil aktiv.
- **Phase 3:** Moderations-Events in DB sichtbar, `/delete_my_data` Befehl funktioniert, Auto-Löschung nach 30 Tagen
- **Phase 4:** Bekanntes Deepfake-Bild wird mit Score >0.7 erkannt, Video-Frames werden extrahiert
- **Phase 5:** Dashboard zeigt Statistiken, Admin kann `/stats` im Chat nutzen, Educational Feedback sprachspezifisch
- **Phase 6:** Signal-Bot antwortet, K8s Deployment läuft, `pip install deepfake-guardian-lang-fr` möglich

---

## i18n-Architektur (Querschnitt über alle Phasen)

```
engine/i18n/
├── __init__.py          # Sprach-Registry
├── base.py              # LanguagePack ABC
├── registry.py          # Auto-Discovery & Plugin-Loading
├── detector.py          # Spracherkennung → Pack-Routing
└── packs/
    ├── __init__.py
    ├── de.py            # Phase 2: Deutsch (ML-Modell + Patterns + Hilfsangebote)
    ├── en.py            # Phase 2: Englisch (migriert BART)
    ├── fr.py            # Phase 6: Französisch (Community)
    └── ...              # Weitere Sprachen

telegram-bot/i18n/
├── loader.py            # JSON-Loader mit Fallback
├── de.json              # Bot-UI-Texte Deutsch
├── en.json              # Bot-UI-Texte Englisch
└── ...

whatsapp-bot/src/i18n/
├── loader.ts            # i18n-Loader
├── de.json              # Bot-UI-Texte Deutsch
├── en.json              # Bot-UI-Texte Englisch
└── ...
```

**LanguagePack Interface:**
```python
class LanguagePack(ABC):
    lang_code: str                    # "de", "en", "fr", ...
    lang_name: str                    # "Deutsch", "English", ...

    def detect(text) -> float         # Sprach-Konfidenz 0.0-1.0
    def get_classifier() -> Callable  # Sprachspezifisches ML-Modell
    def get_patterns() -> list        # Regex/Keyword-Patterns
    def get_labels() -> dict          # Lokalisierte Kategorie-Namen
    def get_educational_messages()    # Educational feedback messages
    def get_helplines() -> list       # Local support resources
```

**Neues Sprachpaket hinzufügen = 1 Datei:**
```python
# engine/i18n/packs/fr.py
class FrenchPack(LanguagePack):
    lang_code = "fr"
    lang_name = "Français"
    # ... implement methods
```
→ Wird automatisch von der Registry entdeckt und aktiviert (wenn in ENABLED_LANGUAGES).

---

## Kritische Dateien (meistmodifiziert über alle Phasen)

- `engine/classifiers.py` — Kern der Klassifikation → delegiert an i18n-Router (Phase 2, 4)
- `engine/i18n/` — Sprachpakete und Registry (Phase 2, 6)
- `engine/routes.py` — API-Endpunkte (jede Phase)
- `engine/models.py` — Datenmodelle (Phase 2, 3)
- `engine/config.py` — Konfiguration (jede Phase)
- `engine/verdict.py` — Entscheidungslogik (Phase 2, 3)
- `telegram-bot/main.py` — Bot-Logik (Phase 2, 3, 5)
- `docker-compose.yml` — Service-Orchestrierung (Phase 3, 5)

---

## Internationalisierungs-Strategie als USP

| Aspekt | Deepfake Guardian | Typische Konkurrenz |
|--------|-------------------|---------------------|
| Sprachen | Plugin-System, Community-erweiterbar | English-only oder manuell hinzugefügt |
| Kultureller Kontext | Pro Sprache: Patterns, Hilfsangebote, Gesetze | Einheitsmodell |
| Datenschutz | DSGVO-first (höchstes Niveau weltweit) | Oft US-centric, minimal |
| Neue Sprache | 1 Python-Datei + 1 JSON | Wochen/Monate Entwicklung |
| Zielgruppe | Von Minderjährigen bis Unternehmen (strengster Schutz als Default) | Generisch |

> **Das hohe Maß an Datenschutz wird in anderen Ländern ein großer Pluspunkt sein** — DSGVO-Compliance für Minderjährige ist der strengste Standard weltweit. Wer diesen erfüllt, erfüllt automatisch auch COPPA (USA), PIPEDA (Kanada), LGPD (Brasilien), etc. Auch Unternehmen und Organisationen profitieren von diesem Datenschutzniveau.
