/**
 * WhatsApp moderation bot using Baileys.
 *
 * Connects to WhatsApp via QR code, listens for group messages,
 * and moderates content through the engine API.
 */

import makeWASocket, {
  DisconnectReason,
  downloadMediaMessage,
  useMultiFileAuthState,
  type WAMessage,
  type WASocket,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import pino from "pino";
import * as qrcode from "qrcode-terminal";

import { config } from "./config";
import {
  moderateImage,
  moderateText,
  moderateVideo,
  type ModerationResult,
} from "./engine-client";

const logger = pino({ level: config.logLevel });

// ---------------------------------------------------------------------------
// Verdict handling
// ---------------------------------------------------------------------------

async function handleVerdict(
  sock: WASocket,
  message: WAMessage,
  result: ModerationResult
): Promise<void> {
  const jid = message.key.remoteJid;
  if (!jid || result.verdict === "allow") return;

  logger.info(
    { verdict: result.verdict, reasons: result.reasons, jid },
    "moderation_action"
  );

  if (result.verdict === "delete") {
    // Try to delete the message (requires admin rights)
    try {
      await sock.sendMessage(jid, { delete: message.key });
      logger.info({ messageId: message.key.id }, "message_deleted");
    } catch {
      // Not admin — notify the group instead
      await notifyAdmins(sock, jid, result.reasons);
    }
  } else if (result.verdict === "flag") {
    await notifyAdmins(sock, jid, result.reasons);
  }
}

async function notifyAdmins(
  sock: WASocket,
  groupJid: string,
  reasons: string[]
): Promise<void> {
  try {
    const metadata = await sock.groupMetadata(groupJid);
    const adminMentions = metadata.participants
      .filter((p) => p.admin)
      .map((p) => p.id);

    const reasonText = reasons.join(", ");
    await sock.sendMessage(groupJid, {
      text: `⚠️ Flagged content (${reasonText}). Admins have been notified.`,
      mentions: adminMentions,
    });
  } catch (err) {
    logger.error({ err, groupJid }, "failed_to_notify_admins");
  }
}

// ---------------------------------------------------------------------------
// Message processing
// ---------------------------------------------------------------------------

function isGroupMessage(message: WAMessage): boolean {
  return message.key.remoteJid?.endsWith("@g.us") === true;
}

async function processMessage(
  sock: WASocket,
  message: WAMessage
): Promise<void> {
  if (!isGroupMessage(message)) return;
  if (message.key.fromMe) return; // Don't moderate own messages

  const msg = message.message;
  if (!msg) return;

  try {
    let result: ModerationResult | null = null;

    // Text messages
    const text = msg.conversation ?? msg.extendedTextMessage?.text;
    if (text) {
      result = await moderateText(text);
    }

    // Image messages
    if (msg.imageMessage) {
      const buffer = (await downloadMediaMessage(
        message,
        "buffer",
        {}
      )) as Buffer;
      result = await moderateImage(buffer);
    }

    // Video messages
    if (msg.videoMessage) {
      const buffer = (await downloadMediaMessage(
        message,
        "buffer",
        {}
      )) as Buffer;
      result = await moderateVideo(buffer);
    }

    if (result) {
      await handleVerdict(sock, message, result);
    }
  } catch (err) {
    logger.error({ err, messageId: message.key.id }, "moderation_error");
  }
}

// ---------------------------------------------------------------------------
// Connection
// ---------------------------------------------------------------------------

async function startBot(): Promise<void> {
  const { state, saveCreds } = await useMultiFileAuthState(
    config.sessionDataPath
  );

  const sock = makeWASocket({
    auth: state,
    logger: pino({ level: "silent" }) as any,
    printQRInTerminal: false,
  });

  // QR code display
  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      logger.info("Scan the QR code below to connect:");
      qrcode.generate(qr, { small: true });
    }

    if (connection === "close") {
      const statusCode = (lastDisconnect?.error as Boom)?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      logger.info(
        { statusCode, shouldReconnect },
        "connection_closed"
      );
      if (shouldReconnect) {
        startBot();
      }
    } else if (connection === "open") {
      logger.info("whatsapp_bot_connected");
    }
  });

  sock.ev.on("creds.update", saveCreds);

  // Listen for new messages
  sock.ev.on("messages.upsert", async ({ messages }) => {
    for (const msg of messages) {
      await processMessage(sock, msg);
    }
  });
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

logger.info({ engineUrl: config.engineUrl }, "starting_whatsapp_bot");
startBot().catch((err) => {
  logger.fatal({ err }, "failed_to_start_bot");
  process.exit(1);
});
