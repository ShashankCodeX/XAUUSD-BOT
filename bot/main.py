"""Gold Wolf Bot: Telegram commands for XAUUSD (Version 1).

Run it from the project folder with:  python -m bot.main
"""
from __future__ import annotations

import asyncio
import functools
import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv
from telegram import Update
from telegram.error import InvalidToken, NetworkError
from telegram.ext import Application, CommandHandler, ContextTypes

from bot import data, news, risk, sessions
from bot.journal import Journal

logger = logging.getLogger("goldbot")

HELP_TEXT = """Gold Wolf Bot (XAUUSD tools)

/gold - price, open sessions, news warning
/session - session clock in your time zone
/news - high-impact USD events, next 24h
/size RISK STOP - lot size. Example: /size 30 3
/spread SPREAD TARGET - spread vs target. Example: /spread 0.35 6
/log buy|sell ENTRY STOP TARGET [note] - save a trade plan
/result ID R - save the result in R. Example: /result 3 -1
/journal - your last 10 trades and total R
/whoami - show your Telegram user id

Educational tool only. Not financial advice."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_allowed(update: Update) -> bool:
    owner = os.getenv("ALLOWED_USER_ID", "").strip()
    if not owner:
        return True  # open mode (a warning is printed at startup)
    user = update.effective_user
    return user is not None and str(user.id) == owner


def guarded(handler):
    """Only let the owner (ALLOWED_USER_ID) use a command."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update):
            if update.message:
                await update.message.reply_text("Sorry, this bot is private.")
            return
        await handler(update, context)

    return wrapper


def display_tz(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.application.bot_data["tz"]


def fmt_event(event: news.Event, tz_name: str) -> str:
    local = event.time_utc.astimezone(ZoneInfo(tz_name))
    extra = []
    if event.forecast:
        extra.append(f"forecast {event.forecast}")
    if event.previous:
        extra.append(f"previous {event.previous}")
    tail = f" ({', '.join(extra)})" if extra else ""
    return f"{local:%a %H:%M}  {event.title}{tail}"


# ---------- commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Your Telegram user id is {user.id}\n\n"
        f"To make the bot private, add this line to your .env file and restart the bot:\n"
        f"ALLOWED_USER_ID={user.id}"
    )


@guarded
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_name = display_tz(context)
    now = utc_now()
    lines = []

    try:
        quote = await asyncio.to_thread(data.get_quote)
        local = quote.time_utc.astimezone(ZoneInfo(tz_name))
        lines.append(f"Gold ({quote.symbol} futures): ${quote.price:,.2f}")
        lines.append(f"Last 5-min candle: {local:%a %H:%M} ({tz_name})")
        age = quote.age_minutes(now)
        if age > 20:
            lines.append(f"Warning: this price is {age:.0f} min old. The market may be closed, or the free feed is lagging.")
    except Exception:
        logger.exception("Price fetch failed")
        lines.append("Couldn't get the gold price right now. Try again in a minute.")

    lines.append("")
    lines.append(sessions.describe_sessions(now, tz_name).split("\n\n")[0])

    try:
        events = await asyncio.to_thread(news.fetch_events)
        hit = news.news_guard(events, now)
        lines.append("")
        if hit:
            lines.append(f"NEWS GUARD: high-impact USD news within 15 minutes!\n{fmt_event(hit, tz_name)}\nBest to stay out until the spike settles.")
        else:
            lines.append("News guard: no high-impact USD news within 15 minutes.")
    except news.NewsUnavailable:
        lines.append("")
        lines.append("News guard: calendar unavailable. Check the calendar manually before trading.")

    lines.append("")
    lines.append("Futures price is delayed and differs slightly from spot XAUUSD. Use your broker's price to trade.")
    await update.message.reply_text("\n".join(lines))


@guarded
async def session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(sessions.describe_sessions(utc_now(), display_tz(context)))


@guarded
async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_name = display_tz(context)
    try:
        events = await asyncio.to_thread(news.fetch_events)
    except news.NewsUnavailable:
        await update.message.reply_text("The news calendar is unavailable right now. Check a calendar manually until it's back.")
        return
    items = news.upcoming(events, utc_now())
    if not items:
        await update.message.reply_text("No high-impact USD events in the next 24 hours.")
        return
    body = "\n".join(fmt_event(e, tz_name) for e in items)
    await update.message.reply_text(f"High-impact USD events (times in {tz_name}):\n{body}")


@guarded
async def size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = "Usage: /size RISK STOP\nExample: /size 30 3 (risk $30 with a $3 stop distance)"
    if len(context.args) != 2:
        await update.message.reply_text(usage)
        return
    try:
        risk_usd, stop_usd = float(context.args[0]), float(context.args[1])
    except ValueError:
        await update.message.reply_text("Both values must be numbers.\n" + usage)
        return
    try:
        result = risk.lot_size(risk_usd, stop_usd)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    await update.message.reply_text(
        f"Lot size: {result.lots:.2f} lots ({result.ounces:.0f} oz)\n"
        f"Risk if stopped out: ${result.actual_risk:.2f}\n\n"
        f"Stop distance = the price gap between entry and stop (entry 2650.00, stop 2647.00 = 3.00).\n"
        f"Assumes 1 lot = 100 oz. Check your broker's contract size."
    )


@guarded
async def spread_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = "Usage: /spread SPREAD TARGET\nExample: /spread 0.35 6 (spread $0.35, target distance $6)"
    if len(context.args) != 2:
        await update.message.reply_text(usage)
        return
    try:
        share = risk.spread_share(float(context.args[0]), float(context.args[1]))
    except ValueError as exc:
        await update.message.reply_text(f"{exc}\n{usage}")
        return
    if share <= 0.10:
        verdict = "OK: the spread is small compared with your target."
    elif share <= 0.20:
        verdict = "Borderline: the spread eats a noticeable part of your target."
    else:
        verdict = "Too high: skip this scalp or widen the target."
    await update.message.reply_text(f"The spread is {share:.1%} of your target.\n{verdict}")


@guarded
async def log_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = "Usage: /log buy|sell ENTRY STOP TARGET [note]\nExample: /log buy 2650 2647 2656 london breakout"
    args = context.args
    if len(args) < 4 or args[0].lower() not in ("buy", "sell"):
        await update.message.reply_text(usage)
        return
    side = args[0].lower()
    try:
        entry, stop, target = (float(x) for x in args[1:4])
    except ValueError:
        await update.message.reply_text("Entry, stop and target must be numbers.\n" + usage)
        return
    try:
        plan = risk.plan_from_prices(entry, stop, target)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    if plan.side != side:
        await update.message.reply_text(
            f"Those prices describe a {plan.side.upper()}, but you typed {side}. Check them and try again."
        )
        return
    journal: Journal = context.application.bot_data["journal"]
    trade_id = journal.add(side, entry, stop, target, plan.rr, " ".join(args[4:]))
    await update.message.reply_text(
        f"Saved trade #{trade_id}: {side.upper()} {entry:g}, stop {stop:g}, target {target:g}\n"
        f"Reward:risk = 1:{plan.rr:.2f}\n"
        f"When it finishes, record it: /result {trade_id} R (for example /result {trade_id} -1)"
    )


@guarded
async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = "Usage: /result ID R\nExample: /result 3 -1 (lost 1R) or /result 3 2.5 (won 2.5R)"
    if len(context.args) != 2:
        await update.message.reply_text(usage)
        return
    try:
        trade_id, r_value = int(context.args[0]), float(context.args[1])
    except ValueError:
        await update.message.reply_text("ID must be a whole number and R a number.\n" + usage)
        return
    journal: Journal = context.application.bot_data["journal"]
    if journal.set_result(trade_id, r_value):
        await update.message.reply_text(f"Saved: trade #{trade_id} result {r_value:+g}R")
    else:
        await update.message.reply_text(f"No trade with id {trade_id}. See /journal.")


@guarded
async def journal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    journal: Journal = context.application.bot_data["journal"]
    rows = journal.recent(10)
    if not rows:
        await update.message.reply_text("Your journal is empty. Add a plan with /log.")
        return
    lines = []
    for row in rows:
        result = "open" if row["result_r"] is None else f"{row['result_r']:+g}R"
        note = f" - {row['note']}" if row["note"] else ""
        lines.append(
            f"#{row['id']} {row['side'].upper()} {row['entry']:g} / SL {row['stop']:g} / TP {row['target']:g} "
            f"(1:{row['rr']:.1f}) {result}{note}"
        )
    stats = journal.stats()
    if stats["closed"]:
        win_rate = stats["wins"] / stats["closed"]
        lines.append("")
        lines.append(
            f"Closed trades: {stats['closed']} | Total: {stats['total_r']:+.2f}R | Win rate: {win_rate:.0%}"
        )
    await update.message.reply_text("\n".join(lines))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled error", exc_info=context.error)


# ---------- startup ----------

def build_application(token: str, tz_name: str, journal: Journal) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data["tz"] = tz_name
    app.bot_data["journal"] = journal
    for name, handler in (
        ("start", start),
        ("help", start),
        ("whoami", whoami),
        ("gold", gold),
        ("session", session_cmd),
        ("news", news_cmd),
        ("size", size),
        ("spread", spread_cmd),
        ("log", log_trade),
        ("result", result_cmd),
        ("journal", journal_cmd),
    ):
        app.add_handler(CommandHandler(name, handler))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    # override=True: the .env file wins over any old value left in the terminal.
    load_dotenv(override=True)
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    # These libraries print the full request URL, which contains your bot token.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_TOKEN is missing. Add it to your .env file (see .env.example).")

    tz_name = os.getenv("DISPLAY_TZ", "Asia/Kolkata").strip()
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise SystemExit(f"DISPLAY_TZ '{tz_name}' is not a valid time zone (example: Asia/Kolkata).")

    if not os.getenv("ALLOWED_USER_ID", "").strip():
        logger.warning("ALLOWED_USER_ID is not set: anyone who finds your bot can use it. Send /whoami to the bot to get your id.")

    app = build_application(token, tz_name, Journal())
    # Newer Python versions no longer create an event loop automatically.
    asyncio.set_event_loop(asyncio.new_event_loop())
    logger.info("Gold Wolf Bot is running. Press Ctrl+C to stop.")
    try:
        app.run_polling()
    except InvalidToken:
        # 'from None' hides the long error, which would print the token.
        raise SystemExit(
            "Telegram rejected the token. Get a fresh one from @BotFather (/revoke) and update .env."
        ) from None
    except NetworkError:
        raise SystemExit(
            "Can't reach Telegram. Check your internet connection and try again."
        ) from None


if __name__ == "__main__":
    main()
