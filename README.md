

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

```
trading_bot/
│
├── main.py
├── config.py
├── requirements.txt
│
├── bot/              # Telegram UI layer
├── core/             # Pure business logic
├── services/         # APIs, event bus
├── data/             # DB, models, schemas, repo
└── utils/            # Helpers
```

(See the full architecture document inside the project.)

---

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
