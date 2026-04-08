# Mister Alert: The Vanguard Architecture 🚀

**Mister Alert** is an institutional-grade, highly-available trading companion designed to monitor forex and crypto markets, alert users to critical price movements, and operate an autonomous internal economy.

This repository is built using "Senior Developer" patterns. It is self-healing, structurally immune to junior coding mistakes via its "Digital Constitution", and heavily fortified for production on a VPS.

## 🏗️ The Architectural Layout

The system is modeled after human anatomy to enforce strict separation of concerns:

1. **The Senses (Services Layer)**: Handles all external connections. It talks to Binance/Twelve Data for prices and manages subscription limits. It passes data inwards but knows nothing of the UI.
2. **The Brain (Core Layer)**: Pure business logic. It handles risk calculation algorithms, target processing, and pure data math.
3. **The Memory (Data Layer)**: The `AsyncSession` database controllers. Repositories handle all PostgreSQL interactions safely and cleanly.
4. **The Mouth (Bot Layer)**: The `aiogram` Telegram interface. It handles user interactions, parsing commands, and displaying menus.

**The Nervous System**: Connecting all of this is the `EventBus`, allowing deep core processes to trigger Telegram messages without actually importing the telegram bot module.

## 💰 The Voucher Economy (Monetization)

For maximum security and to eliminate trust issues with unknown users, Mister Alert utilizes a **"Voucher Economy"**. 
- Direct Bot payments (Bank/Crypto) are hidden by default via the `SettingsRepository`.
- Users must click **"Redeem Activation Code"**. 
- Admins act as **The Mint**. They sell codes externally (M-Pesa, Cash, Escrow) and use a private `/admin` dashboard to generate cryptographically secure, single-use keys (`PREM-XYZ12345`).
- Once a code is redeemed, the DB marks it as "Burned", preventing double spends.

## ⚡ High-Availability & Self-Healing

Mister Alert is designed to never require server reboots for operational changes:
- **God Mode Backdoor**: If the primary admin loses their Telegram account, they do not need SSH access to regain control. By messaging the bot the encrypted `god_key` (stored in the DB), they are instantly elevated to Admin, and the key automatically regenerates to prevent replay attacks.
- **Dynamic Vendor Pipes**: The official vendor link can be swapped out live from the Admin Dashboard.
- **The Absolute Shield**: `architecture_inspector.py` runs on every boot. If any code imports are "messy" (e.g., using relative imports instead of `app.X`), the bot refuses to boot and logs the exact error. It acts as an automated Senior Dev code reviewer.

## 📊 Analytics & Admin Intelligence

The bot is embedded with a comprehensive `admin/stats.py` module. It tracks:
- Total user growth and 7-day trailing metrics.
- Active premium subscriptions.
- Active trade and alert counts safely monitored without invading user privacy.
- Capable of generating `mister_alert_users.csv` on the fly for marketing exports directly through Telegram.

## 🛠️ Developer Quick Start

If you are an AI or Developer hired to work on this code, **respect the architecture**.

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Setup PostgreSQL & Redis**: Essential for the FSM states and the Memory layer.
3. **Database Migration**: `alembic upgrade head`
4. **Testing Pipeline**: Run `pytest tests/` before pushing. Features like the Voucher Economy rely on CI/CD proofs before deploying.
5. **Boot**: `python main.py`
