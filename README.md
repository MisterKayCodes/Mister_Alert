# Mister Alert: The Vanguard Architecture 🚀

**Mister Alert** is an institutional-grade, highly-available trading platform designed to monitor global markets, automate engagement, and operate a self-sustaining internal economy.

This repository is built with **Zero-Trust Engineering**. It is protected by a "Digital Constitution" and an "Intelligent Diagnostic Engine" that ensures every line of code adheres to elite architectural standards.

---

## 🏗️ The Architectural Layout (Human Centric)

The system is modeled after human anatomy to enforce strict separation of concerns:

1.  **The Senses (Provider Layer)**: Monitors market data (Gold, BTC, EURUSD). It knows nothing of the dashboard; it only feeds the system raw metrics.
2.  **The Brain (Service Layer)**: Pure business logic. Manages alerts, signals, and marketing strategy.
3.  **The Memory (Data Layer)**: Secure PostgreSQL repositories using `AsyncSession`. Data is untouchable except through defined repository interfaces.
4.  **The Mouth (Interface Layer)**: The `aiogram` Telegram bot. High-aesthetics, 3-per-row grid menus, and an advanced Marketing Dashboard.

**The Nervous System**: An asynchronous `EventBus` bridges these layers, allowing the "Brain" to send a signal to the "Mouth" without them being inextricably linked.

---

## 🛡️ The Guardian Suite (Advanced DevOps)

Mister Alert is "Self-Healing" via two professional-grade local systems:

### 1. The Digital Constitution
Before the bot ever touches the market, it runs a pre-flight "Pre-flight Check".
- **Architecture Inspector**: Enforces strict layer boundaries. If a service tries to import from a router, the system aborts boot.
- **Bot Integrity Shield**: Scans every command and button in the code. If a single button exists without a handler, the bot will not start.

### 2. Mister Diagnostics (Shared Intelligence)
If the bot crashes or violates a rule, it triggers **Mister Diagnostics**. 
- It maps the error to the specific project layer.
- It consults a **Deep Pattern Brain** to explain *why* it failed in plain Senior Dev English.
- It is a shared tool, portable to any `Mister` project.

---

## 💰 The Voucher Economy & Marketing Engine

### Monetization
Mister Alert utilizes a **"Voucher Economy"** to eliminate payment friction. Admins act as **The Mint**, generating cryptographically secure codes that users redeem for credits or Premium access.

### Mister Marketing Engine (MME)
A growth layer that uses human-like automated outreach:
- **Keyword Hits**: Automatically replies to relevant messages in target groups with high-conversion templates.
- **Evergreen Templates**: Pre-loaded with professional messaging for Gold and Crypto (weekend aware).
- **Safety Limits**: Hard-coded rate limits and randomized human delays to ensure account longevity.

---

## 🛠️ Global Shared Tools

This project utilizes `C:\Kaycris\mister_tools\`, a shared repository of diagnostic and healing tools designed to maintain high code quality across the entire Mister ecosystem.

---

## 📋 Quick Start (Senior Dev Only)

1. **Install Gear**: `pip install -r requirements.txt`
2. **Infrastructure**: Setup PostgreSQL and run `alembic upgrade head`.
3. **Seed Memory**: `python app/data/seeder.py` to pre-load evergreen templates.
4. **Boot Strategy**: `python main.py`

*Failure to respect the architecture will trigger a Diagnostic Failure.* 🏁
