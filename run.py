#!/usr/bin/env python3
# run.py — Single entry point for Salon Bot v3
# Usage: python3 run.py

import asyncio
import logging
import os
import sys
import threading

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn


def run_backend():
    """Run FastAPI backend in a background thread."""
    uvicorn.run(
        "backend.app:app",          # ← points to backend/app.py
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="warning",
        reload=False,
    )


async def run_bot():
    """Run Telegram bot with reminder scheduler."""
    from config import BOT_TOKEN
    from database.schema import init_db
    from bot.reminders import send_reminders
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler
    from telegram import Update

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    from bot.bot import (
        start, book_cmd, help_cmd,
        admin_cmd, bookings_today_cmd, revenue_today_cmd,
        clients_cmd, export_cmd, status_cmd,
        setname_cmd, sethours_cmd, addservice_cmd, addstaff_cmd,
        handle_callback,
    )

    app.add_handler(CommandHandler("start",          start))
    app.add_handler(CommandHandler("book",           book_cmd))
    app.add_handler(CommandHandler("help",           help_cmd))
    app.add_handler(CommandHandler("admin",          admin_cmd))
    app.add_handler(CommandHandler("bookings_today", bookings_today_cmd))
    app.add_handler(CommandHandler("revenue_today",  revenue_today_cmd))
    app.add_handler(CommandHandler("clients",        clients_cmd))
    app.add_handler(CommandHandler("export",         export_cmd))
    app.add_handler(CommandHandler("status",         status_cmd))
    app.add_handler(CommandHandler("setname",        setname_cmd))
    app.add_handler(CommandHandler("sethours",       sethours_cmd))
    app.add_handler(CommandHandler("addservice",     addservice_cmd))
    app.add_handler(CommandHandler("addstaff",       addstaff_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.create_task(send_reminders(app.bot)),
        "interval", minutes=15, id="reminders"
    )
    scheduler.start()
    logger.info("[SCHEDULER] Reminders started (every 15 min)")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("✦ Salon Bot v3 live")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main():
    # Start FastAPI in background thread
    t = threading.Thread(target=run_backend, daemon=True)
    t.start()
    logger.info(f"[BACKEND] Started on port {os.getenv('PORT', 8000)}")

    # Run bot in main loop
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
