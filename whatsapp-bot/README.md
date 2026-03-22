# WhatsApp Moderation Bot

Monitors WhatsApp group chats for harmful content using the moderation engine API.

## Features

- Connects via QR code (Baileys multi-device)
- Listens for text, image, and video messages in groups
- Sends content to the moderation engine for analysis
- Deletes harmful content if the bot account is a group admin
- Notifies admins otherwise

## Setup

1. Install dependencies:
   ```bash
   cd whatsapp-bot
   npm install
   ```
2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```
3. Build and start:
   ```bash
   npm run build
   npm start
   ```
4. Scan the QR code displayed in the terminal with WhatsApp

> **Note:** The WhatsApp account used becomes the bot. Use a dedicated number.
