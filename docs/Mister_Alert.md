# Mister Alert — System Architecture & Build Log

> This document is the single source of truth for the Mister Alert project.
> Any AI or human developer should read this first before touching the code.

---

# 1️⃣ What This Project Is

Mister Alert is a modular trading assistant that provides:

- Price alerts
- Trade tracking (TP / SL)
- Risk & position calculators
- CSV trade analysis
- Telegram bot UI

Design goals:

- Business logic is framework-independent
- UI is replaceable (Telegram today, Web tomorrow)
- Everything communicates via events
- No tight coupling between systems

---

# 2️⃣ Architecture Rules (DO NOT BREAK)

- `core/` contains PURE business logic
- `bot/` contains ONLY Telegram code
- `services/` contains external integrations
- `data/` contains DB only
- `core/` NEVER imports:
  - bot
  - data
  - services

- Communication:
  - Core → emits events
  - Services / Bot → subscribe to events

---

# 3️⃣ Folder Responsibilities

## bot/
Telegram UI, commands, keyboards, states.

## core/
Business logic engines:
- calculators/
- alerts/
- trades/
- csv/
- validators/
- events.py (event types)

## services/
- event_bus.py
- price providers
- external APIs

## data/
- models
- database
- repositories

---

# 4️⃣ Event System (Central Nervous System)

## Event Types

- PriceUpdateEvent
- AlertTriggeredEvent
- AlertExpiredEvent
- TradeOpenedEvent
- TakeProfitHitEvent
- StopLossHitEvent
- CsvImportedEvent

Location:
- core/events.py
- services/event_bus.py

Status: ✅ IMPLEMENTED

---

# 5️⃣ Engines (Business Logic)

## 5.1 Calculators — core/calculators/

- Pips calculator ✅ DONE
- Risk/Reward calculator ✅ DONE
- Position size calculator ✅ DONE

Status: ✅ COMPLETE

---

## 5.2 Alert Engine — core/alerts/engine.py

Purpose:
- Receives price updates
- Checks alerts
- Emits:
  - AlertTriggeredEvent
  - AlertExpiredEvent

Status: ⏳ NOT IMPLEMENTED

---

## 5.3 Trade Engine — core/trades/tracker.py

Purpose:
- Tracks open trades
- Checks TP / SL
- Emits:
  - TakeProfitHitEvent
  - StopLossHitEvent

Status: ⏳ NOT IMPLEMENTED

---

## 5.4 CSV Engine — core/csv/

- parser.py → parse CSV ⏳
- analytics.py → compute stats ⏳

Status: ⏳ NOT IMPLEMENTED

---

# 6️⃣ Services

## 6.1 Event Bus

- File: services/event_bus.py
- Purpose:
  - Subscribe
  - Publish
  - Dispatch events

Status: ✅ IMPLEMENTED

---

## 6.2 Price Providers

- Binance ⏳
- TwelveData ⏳

Status: ⏳ NOT IMPLEMENTED

---

# 7️⃣ Data Layer

- SQLAlchemy models ✅
- Alembic migrations ✅
- Repositories ⏳ PARTIAL

Status: ⚠️ IN PROGRESS

---

# 8️⃣ Build Order (Follow This Always)

1. Alert Engine
2. Trade Engine
3. Price Provider
4. Bot integration
5. CSV analytics

---

# 9️⃣ Current Focus

> Building: core/alerts/engine.py

---

# 🔟 Change Log

## 2026-01-XX
- Event system implemented
- Calculators completed
- Architecture finalized

---

# 11️⃣ How To Continue This Project With Any AI

Send this file and say:

> "Follow this architecture. Do not break the rules. Continue from Current Focus."
