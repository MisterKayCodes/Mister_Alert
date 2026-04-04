Got it! Here’s a **comprehensive README.md** for Mister Alert incorporating everything you specified — updated project tree with `docs/` and `tests/`, plus the dependencies list with brief explanations.

---

```markdown
# 🚨 Mister Alert

**Mister Alert** is a modular, event-driven trading assistant for **crypto and forex** that tracks:

* 📈 Price alerts  
* 🎯 TP / SL hits  
* 🧮 Risk & position calculations  
* 📊 Trade analytics (CSV import)  

It is built with **Python, Aiogram, SQLAlchemy, Alembic**, and a **clean scalable architecture** designed for long-term growth.

---

# ✨ Features

* ✅ **Real-time Price Alerts** (Crypto via Binance, Forex via Twelve Data)
* ✅ **Tiered Speed Logic**: Premium (10s latency) vs Free (120s latency)
* ✅ **TP / SL Hit Notifications**
* ✅ **Interactive Trade Tracking**
* ✅ **The Strategist**: Position size, pips, and risk/reward calculators
* ✅ **Subscription Gating**: Built-in limits (3 alerts for Free users)
* ✅ **Conversion Psychology**: Footers and speed-gap reporting to drive upgrades
* ✅ **Admin Command Center**: /admin tools for user management
* ✅ **Event-Driven Architecture**: Clean separation of concerns (Core vs UI vs Services)

---

# 🏗️ Architecture Overview

| Layer       | Role | Components |
| ----------- | ---- | ---------- |
| **Talking** | `bot/` | Dispatcher, Routers, Keyboards, Middlewares |
| **Thinking** | `core/` | Alert Engine, Trade Tracker, Calculators, Events |
| **Fetching** | `services/` | Price Providers (Binance, TwelveData), EventBus |
| **Remembering** | `data/` | Database (SQLite), Repository, Models |

---

# 💎 Subscription Tiers

| Feature | Free Tier | Premium Tier |
| --- | --- | --- |
| **Alert Limit** | 3 Active Alerts | Unlimited |
| **Trade Tracker** | 1 Active Trade | Unlimited |
| **Latency** | 120s (Slow Lane) | 10s (Fast Lane) |
| **Status Footers** | Included | Removed |
| **Support** | Standard | Priority VIP |

---

# 🧠 Mental Model

```

Bot = talks
Core = thinks
Services = fetches
Data = remembers
Events = connects everything

```

---

# 📁 Project Structure

```

Mister_Alert/
│
├── main.py
├── config.py
├── requirements.txt
│
├── bot/                           # 🧑‍💻 UI Layer (Telegram only)
│   ├── **init**.py
│   ├── dispatcher.py             # Bootstraps bot, routers, middlewares, listeners
│   │
│   ├── routers/                  # One file = one feature UI
│   │   ├── start.py
│   │   ├── alerts.py
│   │   ├── calculators.py
│   │   ├── trades.py
│   │   ├── csv_analysis.py
│   │   └── settings.py
│   │
│   ├── keyboards/
│   │   ├── inline.py
│   │   └── reply.py
│   │
│   ├── states/
│   │   ├── alert_states.py
│   │   ├── calculator_states.py
│   │   ├── trade_states.py
│   │   └── csv_states.py
│   │
│   ├── middlewares/
│   │   └── permissions.py        # Free vs Paid gatekeeper
│   │
│   └── notification_handler.py   # 🔔 Listens to events and sends Telegram messages
│
├── core/                          # 🧠 Business Logic (PURE brain)
│   ├── **init**.py
│   │
│   ├── calculators/
│   │   ├── pips.py
│   │   ├── risk_reward.py
│   │   └── position_size.py
│   │
│   ├── alerts/
│   │   └── engine.py             # Alert checking engine (emits events)
│   │
│   ├── trades/
│   │   └── tracker.py            # Trade watcher (TP/SL logic)
│   │
│   ├── csv/
│   │   ├── parser.py
│   │   └── analytics.py
│   │
│   ├── validators/
│   │   ├── prices.py
│   │   └── numbers.py
│   │
│   └── events.py                 # System event definitions (AlertHit, TPHit, etc)
│
├── services/                      # 🌍 External world
│   ├── **init**.py
│   │
│   ├── price_providers/
│   │   ├── base.py               # Interface: get_price(symbol) -> float
│   │   ├── binance.py
│   │   └── twelve_data.py
│   │
│   └── event_bus.py              # Event system (in-memory / Redis / RabbitMQ)
│
├── data/                          # 🗄️ Memory & Data Shapes
│   ├── database.py               # DB connection
│   ├── models.py                 # SQLAlchemy models (tables)
│   ├── schemas.py                # Pydantic schemas (data shapes)
│   └── repository.py             # All DB operations
│
├── docs/                          # 📚 System truth
│   ├── Mister_Alert.md           # 🧠 Master architecture document
│   └── Mister_Rulebook.md        # 📜 Coding and design rules
│
├── tests/                         # 🧪 Tests & manual runners
│   ├── run_position_size.py
│   ├── run_risk_reward.py
│   └── test_calculators.py
│
└── utils/
├── logger.py
└── helpers.py

````

---

# ⚙️ Tech Stack & Dependencies

* **Python 3.11+** – Modern Python version  
* **aiogram==3.4.1** – Async Telegram bot framework  
* **pydantic==2.5.2** & **pydantic-settings==2.2.1** – Data validation and settings management  
* **SQLAlchemy==2.0.25** – Async ORM for database access  
* **alembic==1.13.0** – Database migrations  
* **aiosqlite==0.19.0** – Async SQLite driver  
* **httpx==0.26.0** – Async HTTP client for external APIs  
* **taskiq==0.11.7** – Async background task processing  
* **anyio==4.2.0** – Async networking and concurrency foundation  
* **loguru==0.7.2** – Structured logging library  
* **python-dateutil==2.8.2** – Date parsing and utilities  
* **orjson==3.9.10** – Fast JSON serialization/deserialization  

---

# 🚀 Setup & Installation

1. **Clone repo**

   ```bash
   git clone https://github.com/YOUR_USERNAME/Mister_Alert.git
   cd Mister_Alert
````

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**

   ```env
   BOT_TOKEN=your_telegram_bot_token

   COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
   EXCHANGE_RATE_BASE_URL=https://api.exchangerate.host

   DATABASE_URL=sqlite+aiosqlite:///./Mister_alert.db
   ```

5. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

6. **Run the bot**

   ```bash
   python main.py
   ```

---

# 🧩 Key Design Principles

* Event-driven architecture
* Strict separation of concerns and layers
* Replaceable UI and API providers
* Testable, maintainable core business logic
* Scalable for future growth

---

# 🧪 Future Roadmap

* Web dashboard interface
* Multi-user subscription plans
* Strategy analytics & reporting
* Additional brokers & price APIs
* Backtesting engine
* Subscription billing system
* Cloud deployment

---

# 🏆 Who This Is For

* Traders looking for automated trade alerts
* Developers building fintech or trading tools
* Anyone wanting a robust, maintainable trading assistant
* Learners exploring clean architecture in Python

---

# 🛡️ License

MIT License (or your preferred license)

---

# 💡 Philosophy

> Build systems that survive feature growth, not scripts that collapse under it.

---

# 🤝 Contributing

Pull requests are welcome. Please respect architecture and code quality.

---

```

---

