# Privacy Policy — Deepfake Guardian

> **Template** — customise for your deployment before making it public.
> Replace `[OPERATOR]`, `[CONTACT]`, `[COUNTRY]`, and `[DATE]` with your details.

---

## 1. Who is responsible?

The controller responsible for data processing is:

**[OPERATOR]**
[Contact address / email: CONTACT]

---

## 2. What data do we process and why?

Deepfake Guardian analyses messages in group chats to detect harmful content
(violence, NSFW material, sexual violence, cyberbullying, and deepfakes).

| Data | Purpose | Legal basis (GDPR) |
|------|---------|-------------------|
| Moderation metadata (verdict, category scores, timestamp) | Safety audit trail | Article 6(1)(f) — legitimate interest in protecting group members |
| Pseudonymous user/group identifiers (SHA-256 hashes) | Warning counter per user; right-to-erasure linking | Article 6(1)(f) |
| Consent records | Track whether the privacy notice was shown | Article 6(1)(c) |

**What we do NOT store:**
- Message text, images, or video content
- Your name, username, or phone number in plain text
- IP addresses

---

## 3. Pseudonymisation

Your Telegram (or WhatsApp) user ID is converted to a one-way SHA-256 hash
before being stored. The hash cannot be reversed to your original ID without
access to a secret key held only by the engine operator.

---

## 4. How long is data kept?

Moderation event logs are automatically deleted after **30 days**
(configurable via `DATA_RETENTION_DAYS`).  Warning counters are kept for the
lifetime of the group bot deployment, unless you submit an erasure request.

---

## 5. Your rights (GDPR Articles 15–22)

| Right | How to exercise |
|-------|----------------|
| Access (Art. 15) | Type `/privacy` in the bot chat or contact [CONTACT] |
| Erasure (Art. 17) | Type `/delete_my_data` in the bot chat |
| Restriction (Art. 18) | Contact [CONTACT] |
| Portability (Art. 20) | Contact [CONTACT] |
| Objection (Art. 21) | Contact [CONTACT] |

Erasure requests are processed within **30 days**.

---

## 6. Recipients and transfers

No data is shared with third parties.  The engine runs entirely on your own
infrastructure (self-hosted Docker containers).  No cloud services or
analytics platforms receive any data.

---

## 7. Supervisory authority

If you believe your data is processed unlawfully you may lodge a complaint
with the supervisory authority in your country ([COUNTRY]).

---

## 8. Changes to this policy

We will announce material changes in the group chat.  The current version is
always available at [URL or location].

*Last updated: [DATE]*
