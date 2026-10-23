# Gold Wolf Bot (XAUUSD tools for Telegram)

A free, open-source Telegram bot for gold (XAUUSD) traders. Version 1 is a set of **safety and planning tools**, not a signal service.

> **Disclaimer:** Educational software only. Not financial advice. Trading gold, especially scalping, carries a high risk of loss. Test on a demo account first. The free data used here is delayed and unofficial.

## Features (Version 1)

| Command | What it does |
|---|---|
| `/gold` | Latest gold futures price, open sessions, and a news-guard warning |
| `/session` | London / New York / Tokyo / Sydney clock in your own time zone (daylight saving handled) |
| `/news` | High-impact USD events in the next 24 hours |
| `/size 30 3` | Lot size for a $30 risk with a $3 stop (assumes 1 lot = 100 oz) |
| `/spread 0.35 6` | How much of your target the spread eats |
| `/log buy 2650 2647 2656` | Save a trade plan and see its reward:risk |
| `/result 3 -1` | Record a finished trade in R |
| `/journal` | Last 10 trades, total R and win rate |
| `/whoami` | Shows your Telegram user id (to make the bot private) |

## Setup

1. Install Python 3.11+ and create a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram and copy the token.
3. Copy `.env.example` to `.env` and paste the token. **Never share or commit `.env`.**
4. Run the bot: `python -m bot.main`
5. Message your bot `/whoami`, put the number in `.env` as `ALLOWED_USER_ID`, and restart. Now only you can use it.

## Tests

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## Data sources and limits

- **Price:** Yahoo Finance via `yfinance`, symbol `GC=F` (COMEX gold futures). Delayed, unofficial, and slightly different from spot XAUUSD.
- **News:** A free public weekly calendar feed. Unofficial, so it may change. The bot says so when it can't load it.
- **Fed odds:** CME FedWatch's API is paid, so it's not included.

## Roadmap

- **v2:** Macro panel (DXY, US 10-year yield), spread filter, daily loss limit
- **v3:** Backtester with spread costs, then session-based signals
- **Later:** Optional WhatsApp reply bot through Meta's official Cloud API (no unofficial libraries)

## Contributing

Issues and pull requests are welcome. Please keep secrets out of commits and add a test for any new maths.

## License

MIT
