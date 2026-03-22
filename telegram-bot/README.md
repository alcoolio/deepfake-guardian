# Telegram Moderation Bot

Monitors group chats for harmful content using the moderation engine API.

## Features

- Listens for text messages, photos, and videos in group chats
- Sends content to the moderation engine for analysis
- Deletes harmful content if the bot has admin rights
- Notifies group admins if the bot cannot delete messages

## Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Copy `.env.example` to `.env` and fill in your bot token
3. Add the bot to your group and grant it admin rights (for auto-deletion)

```bash
cd telegram-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your bot token
python main.py
```
