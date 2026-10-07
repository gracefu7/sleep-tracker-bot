import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class SleepDB:
    def __init__(self, db_path="sleep_data.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sleep_sessions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    bedtime TEXT,
                    wake_time TEXT,
                    duration_hours REAL,
                    quality INTEGER,
                    notes TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def add_sleep(self, user_id, bedtime, wake_time, quality, notes=""):
        duration = self._calc_duration(bedtime, wake_time)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sleep_sessions
                (user_id, bedtime, wake_time, duration_hours, quality, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, bedtime, wake_time, duration, quality, notes, datetime.now().isoformat()))
            conn.commit()

    def get_stats(self, user_id, days=7):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT duration_hours, quality, bedtime, notes FROM sleep_sessions
                WHERE user_id = ? AND created_at > datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """, (user_id, days))
            sessions = cursor.fetchall()

            if not sessions:
                return None

            durations = [s[0] for s in sessions]
            qualities = [s[1] for s in sessions]
            avg_duration = sum(durations) / len(durations)
            avg_quality = sum(qualities) / len(qualities)

            return {
                "count": len(sessions),
                "avg_duration": round(avg_duration, 1),
                "avg_quality": round(avg_quality, 1),
                "sessions": sessions
            }

    def _calc_duration(self, bedtime_str, wake_str):
        try:
            bed = datetime.fromisoformat(bedtime_str)
            wake = datetime.fromisoformat(wake_str)
            if wake < bed:
                wake += timedelta(days=1)
            return round((wake - bed).total_seconds() / 3600, 1)
        except:
            return 0

db = SleepDB()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("😴 Log Sleep", callback_data="log_sleep")],
        [InlineKeyboardButton("📊 View Stats", callback_data="view_stats")],
        [InlineKeyboardButton("💡 Get Insights", callback_data="get_insights")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌙 Welcome to Sleep Tracker!\n\nTrack your sleep and get insights to improve your health.",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "log_sleep":
        await log_sleep_start(query, context)
    elif query.data == "view_stats":
        await view_stats(query, context)
    elif query.data == "get_insights":
        await get_insights(query, context)

async def log_sleep_start(query, context):
    await query.edit_message_text(
        text="📝 Let's log your sleep!\n\nSend your bedtime (format: YYYY-MM-DD HH:MM)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
    )
    context.user_data["state"] = "waiting_bedtime"

async def view_stats(query, context):
    stats = db.get_stats(query.from_user.id, days=7)

    if not stats:
        text = "📊 No sleep data yet. Start logging to see your stats!"
    else:
        text = f"""
📊 Your Sleep Stats (Last 7 days)

Sessions: {stats['count']}
Avg Sleep: {stats['avg_duration']}h
Avg Quality: {stats['avg_quality']}/10

Recent Sessions:
"""
        for duration, quality, bedtime, notes in stats["sessions"][:3]:
            text += f"\n• {bedtime[:10]}: {duration}h (Quality: {quality}/10)"

    await query.edit_message_text(text=text, reply_markup=main_menu())

async def get_insights(query, context):
    stats = db.get_stats(query.from_user.id, days=7)

    if not stats:
        text = "💡 No data for insights yet!"
    else:
        avg = stats["avg_duration"]
        quality = stats["avg_quality"]

        insights = "💡 Your Sleep Insights:\n\n"

        if avg < 6:
            insights += "⚠️ You're getting less sleep than recommended (6-8h). Try to sleep earlier.\n"
        elif avg > 9:
            insights += "📌 You're sleeping more than usual. Consider checking your sleep quality.\n"
        else:
            insights += "✅ Your sleep duration is healthy!\n"

        if quality < 5:
            insights += "😴 Your sleep quality is low. Consider: exercise, less screen time before bed, consistent schedule.\n"
        elif quality > 8:
            insights += "🌟 Excellent sleep quality! Keep your current routine.\n"

        insights += f"\nKeep tracking to see more correlations!"

    await query.edit_message_text(text=insights, reply_markup=main_menu())

def main_menu():
    keyboard = [
        [InlineKeyboardButton("😴 Log Sleep", callback_data="log_sleep")],
        [InlineKeyboardButton("📊 View Stats", callback_data="view_stats")],
        [InlineKeyboardButton("💡 Get Insights", callback_data="get_insights")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") == "waiting_bedtime":
        context.user_data["bedtime"] = update.message.text
        await update.message.reply_text(
            "Got it! Now send your wake time (format: YYYY-MM-DD HH:MM)"
        )
        context.user_data["state"] = "waiting_waketime"

    elif context.user_data.get("state") == "waiting_waketime":
        wake_time = update.message.text
        bedtime = context.user_data.get("bedtime")
        db.add_sleep(update.effective_user.id, bedtime, wake_time, quality=7)
        await update.message.reply_text("✅ Sleep logged!", reply_markup=main_menu())
        context.user_data["state"] = None

async def cancel(query, context):
    context.user_data["state"] = None
    await query.edit_message_text(text="Cancelled.", reply_markup=main_menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))

    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
