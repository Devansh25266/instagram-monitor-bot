import sqlite3
import time
import threading
import os

import instaloader
import schedule

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("8585255621:AAFSprY9LRhfmrXzp3kUbcufycsNQPJUXWk")

# ================= DATABASE =================

conn = sqlite3.connect(
    "tracker.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tracked_accounts (

    username TEXT,
    chat_id INTEGER,
    mode TEXT,
    added_time INTEGER,
    status TEXT
)
""")

conn.commit()

# ================= INSTAGRAM =================

L = instaloader.Instaloader()

def check_instagram(username):

    try:

        instaloader.Profile.from_username(
            L.context,
            username
        )

        return "ACTIVE"

    except Exception as e:

        error = str(e).lower()

        if "not found" in error:
            return "DISABLED"

        return "UNKNOWN"

# ================= TELEGRAM COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📌 Commands\n\n"
        "/ban username\n"
        "/unban username\n"
        "/remove username\n"
        "/list"
    )

    await update.message.reply_text(text)

# ================= BAN TRACKER =================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text(
            "Usage:\n/ban username"
        )

        return

    username = context.args[0].lower()

    status = check_instagram(username)

    cursor.execute("""
    INSERT INTO tracked_accounts
    VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        update.effective_chat.id,
        "BAN",
        int(time.time()),
        status
    ))

    conn.commit()

    await update.message.reply_text(
        f"🚨 Ban Monitor Added\n\n"
        f"Username: @{username}\n"
        f"Current Status: {status}"
    )

# ================= UNBAN TRACKER =================

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text(
            "Usage:\n/unban username"
        )

        return

    username = context.args[0].lower()

    status = check_instagram(username)

    cursor.execute("""
    INSERT INTO tracked_accounts
    VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        update.effective_chat.id,
        "UNBAN",
        int(time.time()),
        status
    ))

    conn.commit()

    await update.message.reply_text(
        f"✅ Unban Monitor Added\n\n"
        f"Username: @{username}\n"
        f"Current Status: {status}"
    )

# ================= REMOVE =================

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:

        await update.message.reply_text(
            "Usage:\n/remove username"
        )

        return

    username = context.args[0].lower()

    cursor.execute("""
    DELETE FROM tracked_accounts
    WHERE username = ?
    """, (username,))

    conn.commit()

    await update.message.reply_text(
        f"❌ Removed @{username}"
    )

# ================= LIST =================

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    rows = cursor.execute("""
    SELECT username, mode, status
    FROM tracked_accounts
    """).fetchall()

    if not rows:

        await update.message.reply_text(
            "No tracked accounts."
        )

        return

    text = "📋 Tracking List\n\n"

    for username, mode, status in rows:

        text += (
            f"@{username}\n"
            f"Mode: {mode}\n"
            f"Status: {status}\n\n"
        )

    await update.message.reply_text(text)

# ================= ALERT =================

async def send_alert(app, chat_id, text):

    await app.bot.send_message(
        chat_id=chat_id,
        text=text
    )

# ================= MONITOR =================

def monitor_accounts(app):

    rows = cursor.execute("""
    SELECT username, chat_id, mode, added_time, status
    FROM tracked_accounts
    """).fetchall()

    current_time = int(time.time())

    for username, chat_id, mode, added_time, old_status in rows:

        # auto remove after 7 days
        if current_time - added_time > 7 * 24 * 3600:

            cursor.execute("""
            DELETE FROM tracked_accounts
            WHERE username = ?
            """, (username,))

            conn.commit()

            continue

        new_status = check_instagram(username)

        # ================= BAN ALERT =================

        if (
            mode == "BAN"
            and old_status == "ACTIVE"
            and new_status == "DISABLED"
        ):

            text = (
                f"🚨 Instagram Account Disabled\n\n"
                f"Username: @{username}"
            )

            app.create_task(
                send_alert(app, chat_id, text)
            )

        # ================= UNBAN ALERT =================

        elif (
            mode == "UNBAN"
            and old_status == "DISABLED"
            and new_status == "ACTIVE"
        ):

            text = (
                f"✅ Instagram Account Restored\n\n"
                f"Username: @{username}"
            )

            app.create_task(
                send_alert(app, chat_id, text)
            )

        cursor.execute("""
        UPDATE tracked_accounts
        SET status = ?
        WHERE username = ?
        """, (
            new_status,
            username
        ))

        conn.commit()

# ================= SCHEDULER =================

def scheduler_thread(app):

    schedule.every(15).minutes.do(
        lambda: monitor_accounts(app)
    )

    while True:

        schedule.run_pending()

        time.sleep(5)

# ================= MAIN =================

app = ApplicationBuilder().token(
    BOT_TOKEN
).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("list", list_accounts))

threading.Thread(
    target=scheduler_thread,
    args=(app,),
    daemon=True
).start()

print("Bot Running...")

app.run_polling()