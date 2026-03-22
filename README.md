# Deepfake Guardian — Content Moderation Monorepo

Open-source moderation system for **Telegram** and **WhatsApp** group chats.
Detects violence, sexual violence, NSFW content, and basic deepfake indicators
in text, images, and videos.

## Architecture

```
┌─────────────┐     HTTP/JSON     ┌──────────────────┐
│ Telegram Bot │ ───────────────▶ │                  │
└─────────────┘                   │  Moderation      │
                                  │  Engine (FastAPI) │
┌──────────────┐    HTTP/JSON     │                  │
│ WhatsApp Bot │ ───────────────▶ │  /moderate_text  │
└──────────────┘                   │  /moderate_image │
                                  │  /moderate_video │
                                  └──────────────────┘
```

| Directory        | Stack                           | Purpose                     |
|------------------|---------------------------------|-----------------------------|
| `engine/`        | Python 3.11, FastAPI            | Content classification API  |
| `telegram-bot/`  | Python, python-telegram-bot     | Telegram group listener     |
| `whatsapp-bot/`  | Node.js, TypeScript, Baileys    | WhatsApp group listener     |

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-org/deepfake-guardian.git
cd deepfake-guardian

# Copy example env files
cp engine/.env.example engine/.env
cp telegram-bot/.env.example telegram-bot/.env
cp whatsapp-bot/.env.example whatsapp-bot/.env
```

### 2. Fill in secrets

- `telegram-bot/.env` → set `TELEGRAM_BOT_TOKEN`
- Adjust thresholds in `engine/.env` if needed

### 3. Run with Docker Compose

```bash
docker compose up --build
```

This starts all three services. The engine downloads ML models on first run
(~1.5 GB) — subsequent starts use the cached volume.

### 4. Run locally (without Docker)

```bash
# Engine
cd engine && pip install -r requirements.txt && python main.py

# Telegram bot (separate terminal)
cd telegram-bot && pip install -r requirements.txt && python main.py

# WhatsApp bot (separate terminal)
cd whatsapp-bot && npm install && npm run build && npm start
```

### 5. Test the engine manually

```bash
curl -X POST http://localhost:8000/moderate_text \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'
```

## How It Works

1. A bot receives a message in a group chat
2. It sends the content (text / image / video) to the engine API
3. The engine runs lightweight ML classifiers and returns a verdict:
   - `"allow"` — content is safe
   - `"flag"` — elevated scores, admins are notified
   - `"delete"` — content exceeds thresholds, deleted if bot is admin
4. If the bot has admin rights it deletes the message; otherwise it @-mentions
   group admins

## Deepfake Detection

> **⚠️ Warning:** Deepfake detection is currently a **stub** that returns a
> fixed score of `0.05`. It is wired into the pipeline so you can drop in a
> real model (e.g. EfficientNet on FaceForensics++) without changing the API
> contract. See `engine/classifiers.py:detect_deepfake_suspect()`.

## Configuration

All services use `.env` files. Key variables:

| Variable                   | Service      | Description                           |
|----------------------------|--------------|---------------------------------------|
| `TELEGRAM_BOT_TOKEN`       | telegram-bot | Token from @BotFather                 |
| `ENGINE_URL`               | bots         | URL of the engine (default: engine:8000) |
| `THRESHOLD_VIOLENCE`       | engine       | Delete threshold for violence (0–1)   |
| `THRESHOLD_SEXUAL_VIOLENCE`| engine       | Delete threshold for sexual violence  |
| `THRESHOLD_NSFW`           | engine       | Delete threshold for NSFW             |
| `THRESHOLD_DEEPFAKE`       | engine       | Delete threshold for deepfake         |

## License

MIT
