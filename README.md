

# 🚨 Mister Alert

**Mister Alert** is a modular, event-driven trading assistant for **crypto and forex** that tracks:

* 📈 Price alerts
* 🎯 TP / SL hits
* 🧮 Risk & position calculations
* 📊 Trade analytics (CSV import)

It is built with **Python, Aiogram, SQLAlchemy, Alembic**, and a **clean scalable architecture** designed for long-term growth.

---

# ✨ Features

* ✅ Price alerts (crypto & forex)
* ✅ TP / SL hit notifications
* ✅ Trade tracking
* ✅ Position size, pips, and risk/reward calculators
* ✅ CSV trade analytics
* ✅ Multi-price API support (CoinGecko, ExchangeRate.host, etc)
* ✅ Event-driven architecture
* ✅ Clean separation of concerns
* ✅ Free & paid feature gating (ready)
* ✅ Built for Telegram (but reusable anywhere)

---

# 🏗️ Architecture Overview

The project is split into **5 independent layers**:

```
User → bot → core → data/services → core → events → bot → User
```

| Layer       | Purpose                      |
| ----------- | ---------------------------- |
| `bot/`      | Telegram UI (talks to users) |
| `core/`     | Business logic (brain)       |
| `services/` | External APIs & integrations |
| `data/`     | Database, models, schemas    |
| `utils/`    | Helpers, logging             |

> ⚠️ The core logic never talks to Telegram, SQL, or APIs directly.

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

Mister_Alert/
│
├── main.py
├── config.py
├── requirements.txt
│
├── bot/                           # 🧑‍💻 UI Layer (Telegram only)
│   ├── __init__.py
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
│   ├── __init__.py
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
│   ├── __init__.py
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
│   └── Mister_Alert.md           # 🧠 Master architecture document
│
├── tests/                         # 🧪 Tests & manual runners
│   ├── run_position_size.py
│   ├── run_risk_reward.py
│   └── test_calculators.py
│
└── utils/
    ├── logger.py
    └── helpers.py


# ⚙️ Tech Stack

* Python 3.11+
* Aiogram v3
* SQLAlchemy 2.0
* Alembic
* Pydantic
* HTTPX
* aiosqlite
* TaskIQ (for background jobs)
* SQLite (for now, swappable later)

---

# 🚀 Setup & Installation

## 1️⃣ Clone repo

```bash
git clone https://github.com/YOUR_USERNAME/Mister_Alert.git
cd Mister_Alert
```

## 2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Create `.env`

```env
BOT_TOKEN=your_telegram_bot_token

COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
EXCHANGE_RATE_BASE_URL=https://api.exchangerate.host

DATABASE_URL=sqlite+aiosqlite:///./Mister_alert.db
```

## 5️⃣ Run migrations

```bash
alembic upgrade head
```

## 6️⃣ Run the bot

```bash
python main.py
```

---

# 🗄️ Database Migrations

Create new migration:

```bash
alembic revision --autogenerate -m "message"
```

Apply migrations:

```bash
alembic upgrade head
```

---

# 🧩 Key Design Principles

* ✅ Event-driven
* ✅ Decoupled layers
* ✅ Replaceable APIs
* ✅ Replaceable UI (Telegram, Web, etc)
* ✅ Testable core logic
* ✅ Long-term maintainability

---

# 🧪 Future Roadmap

* Web dashboard
* Multi-user plans
* Strategy analytics
* More brokers & APIs
* Backtesting engine
* Subscription billing
* Cloud deployment

---

# 🏆 Who This Is For

* Traders
* Developers building fintech tools
* Anyone who wants a **serious trading assistant**
* Anyone who wants to learn **clean architecture**

---

# 🛡️ License

MIT (or choose one)

---

# 💡 Philosophy

> Build systems that survive feature growth, not scripts that collapse under it.

---

# 🤝 Contributing

PRs are welcome.
Architecture discipline is mandatory.

---
