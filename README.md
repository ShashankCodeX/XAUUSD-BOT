# Gold Wolf Bot: XAUUSD tools for Telegram

A free, open-source Telegram bot for gold (XAUUSD) traders. Version 1 gives you **safety and planning tools** (session clock, news guard, lot calculator, trade journal). It does **not** give buy/sell signals.

> **Disclaimer:** Educational software only. Not financial advice. Trading gold, especially scalping, carries a high risk of loss. Test on a demo account first. The free data used here is delayed and unofficial. Use your broker's price to trade.

## What it does

| Command | What it's for |
|---|---|
| `/start` or `/help` | Shows the list of commands |
| `/gold` | Latest gold futures price, which sessions are open, and a news-guard warning |
| `/session` | Clock for the Sydney, Tokyo, London and New York sessions in **your** time zone (daylight saving handled automatically) |
| `/news` | High-impact USD events (CPI, NFP, Fed...) in the next 24 hours |
| `/size 30 3` | Lot size if you risk **$30** with a **$3** stop distance. Assumes 1 lot = 100 oz |
| `/spread 0.35 6` | Shows how much of your **$6** target a **$0.35** spread eats |
| `/log buy 2650 2647 2656 note` | Saves a trade plan (side, entry, stop, target) and shows its reward:risk |
| `/result 3 -1` | Records that trade #3 finished at -1R (use `2.5` for +2.5R) |
| `/journal` | Your last 10 trades, total R and win rate |
| `/whoami` | Shows your Telegram user id, used to make the bot private |

**What is R?** R is your risk on one trade. If you risk $30 and lose it, that is -1R. If you make $60, that is +2R.

## Quick start (about 10 minutes)

You need: a computer with **Python 3.11 or newer**, a free Telegram account, and the free [VS Code](https://code.visualstudio.com/) editor (optional but friendly).

### 1. Get the code

```
git clone https://github.com/ShashankCodeX/XAUUSD-BOT.git
cd XAUUSD-BOT
```

### 2. Create a virtual environment and install

A virtual environment is a private box for this project's libraries.

**Mac / Linux**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

When it is on, your terminal line starts with `(.venv)`.

### 3. Create your Telegram bot

1. In Telegram, open **@BotFather** and send `/newbot`.
2. Choose a name, then a username that ends in `bot`.
3. BotFather sends you a **token**. It works like a password for your bot.

### 4. Add your token

Copy the example settings file, then edit the new `.env` file.

```
cp .env.example .env        # Windows: copy .env.example .env
```

Open `.env` and fill it in. One line each, **no spaces and no quotes**:

```
TELEGRAM_TOKEN=paste_your_token_here
ALLOWED_USER_ID=
DISPLAY_TZ=Asia/Kolkata
```

`DISPLAY_TZ` is the time zone used when the bot shows you times (for example `Europe/London` or `America/New_York`).

### 5. Start the bot

```
python -m bot.main
```

You should see `Gold Wolf Bot is running`. Leave the terminal open: the bot only works while it is running.

### 6. Make the bot private (important)

1. In Telegram, open your bot, press **Start**, and send `/whoami`. It replies with a number.
2. Stop the bot (see below), then put that number in `.env`: `ALLOWED_USER_ID=123456789`
3. Start the bot again. Now only you can use it, and your journal stays private.

## Starting and stopping

| I want to... | Do this |
|---|---|
| **Start** the bot | Open the project folder in a terminal, run `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), then `python -m bot.main` |
| **Stop** the bot | Click the terminal and press `Ctrl + C` |
| **Restart** after changing `.env` | Stop it, then start it again |
| Keep a **Mac awake** while it runs | Start it with `caffeinate -i python -m bot.main` |

The bot stops when you close the terminal or your computer sleeps. For always-on use you need a computer or free cloud machine that stays on.

## Troubleshooting

| What you see | What it means and how to fix it |
|---|---|
| `command not found: python` | On Mac/Linux use `python3` to create the environment. Once `(.venv)` is on, `python` works |
| `No module named 'bot'` | Run the command from the project's main folder, as `python -m bot.main` (not `python bot/main.py`) |
| `TELEGRAM_TOKEN is missing` | The `.env` file is missing, has the wrong name, or the line is empty. Check it is saved |
| `Telegram rejected the token` | The token is wrong or was revoked. In @BotFather send `/revoke`, pick your bot, copy the new token into `.env`, save, and restart |
| `Can't reach Telegram` | Check your internet connection and try again |
| Bot doesn't answer | Make sure the terminal still shows it running. If you set `ALLOWED_USER_ID`, it must be **your** id from `/whoami` |
| `Sorry, this bot is private` | `ALLOWED_USER_ID` doesn't match your Telegram account. Check the number |
| `/gold` says it can't get the price | The free Yahoo feed sometimes fails. Try again in a minute |
| `/news` says the calendar is unavailable | The free calendar feed may be down. Check a calendar website by hand before trading |
| Price looks old | The market may be closed (weekend break) or the free feed is delayed |

## Keeping your token safe

- **Never** commit `.env` to GitHub. It is already in `.gitignore`.
- **Never** paste your token in screenshots, issues or chats.
- If a token is ever exposed, revoke it right away: @BotFather → `/revoke`.
- Before every push, run `git status` and check that `.env` is not listed.

## Data sources and limits

- **Price:** Yahoo Finance through the `yfinance` library, symbol `GC=F` (COMEX gold futures). It is delayed, unofficial, and slightly different from spot XAUUSD.
- **News:** A free public weekly calendar feed. It is unofficial and may change or disappear. The bot tells you when it can't load it.
- **Fed rate odds:** The CME FedWatch API is paid, so it is not included.
- **Lot size:** Assumes 1 lot = 100 oz. Check your broker's contract size.

## Run the tests

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## Roadmap

- **v2:** Macro panel (dollar index, US 10-year yield), spread filter, daily loss limit
- **v3:** Backtester with spread costs, then session-based signals
- **Later:** Optional WhatsApp reply bot using Meta's official Cloud API (no unofficial libraries)

## Contributing

Issues and pull requests are welcome.

- Keep secrets out of commits.
- Add a test for any new maths.
- Run `python -m pytest -q` before you open a pull request.

## License

[MIT](LICENSE). You may use, copy and change this code. It comes with no warranty.
