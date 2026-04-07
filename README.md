# Mister Alert

Mister Alert is a personal trading assistant that does the boring stuff for you. It watches the markets (crypto and forex), waits for your specific targets, and pokes you on Telegram the second something interesting happens. No more staring at charts until your eyes bleed.

## How it works

The system is built like a human to keep things simple:

1. **The Senses (Services)**: This layer is out in the world fetching data. It talks to Binance for crypto and Twelve Data for forex.
2. **The Brain (Core)**: This is where the thinking happens. It doesn't care about databases or Telegram buttons. It just knows if a price hit a target or if a position size is too risky.
3. **The Memory (Data)**: This is the long-term storage. It remembers your alerts, your trades, and your settings using a modular repository system.
4. **The Mouth (Bot/UI)**: This is how it talks to you. It handles the Telegram interface, menus, and notifications.

Everything is connected by a nervous system (the EventBus), so the Brain can tell the Mouth to shout "Bitcoin just hit sixty thousand!" without either layer needing to know how the other works.

## What it can do for you

Position sizing is hard. Watching 10 pairs at once is harder. Mister Alert handles:

- **Price Alerts**: Set it and forget it. You get a notification when the price crosses your line.
- **Trade Monitoring**: It tracks your active trades and alerts you when your take-profit or stop-loss is hit.
- **The Strategist**: A built-in suite of calculators to help you figure out exactly how much to risk on a trade so you don't blow your account.
- **Analytics**: You can import your trading history via CSV and get a clear picture of how you are actually performing. No guessing.

## Why it's "Senior-Grade"

We recently overhauled the entire project to make it modular and stable. 

- **Small Files**: No single file is a giant wall of messy code. Everything is under 200 lines.
- **Clean Layers**: The part that calculates your risk doesn't know what a database is. The part that talks to Telegram doesn't know how to fetch prices. This makes it incredibly easy to fix bugs or add new features.
- **Fast and Slow Lanes**: Built-in logic to prioritize premium users with faster price checks while keeping the standard experience smooth for everyone.

## Quick Start

If you want to run this yourself:

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup your environment**: Create a `.env` file with your Telegram token and API keys (see `config.py` for what you'll need).
3. **Initialize the database**: Use `alembic upgrade head` to set up your tables.
4. **Boot it up**: Run `python main.py`.

## Project Layout

- **app/bot**: The interface layer (routers, keyboards, and middlewares).
- **app/core**: The logic layer (calculators, alert engines, and analytics).
- **app/data**: The storage layer (repositories and database models).
- **app/services**: The external layer (price providers and system events).
- **test**: A suite of integration tests to make sure the "nervous system" is still healthy.

## Contributing

If you want to help make Mister Alert better, keep the code clean, follow the layering rules, and most importantly, keep it simple.

## License

This project is released under the MIT License. Use it, build on it, and go catch some pips.
