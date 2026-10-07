import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:5000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("📱 Open Sleep Tracker", web_app={"url": WEB_APP_URL})
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌙 Welcome to Sleep Tracker!\n\nClick the button below to open the app and start tracking your sleep.",
        reply_markup=reply_markup
    )

def main():
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return

    print("🤖 Starting Sleep Tracker Bot...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("✅ Bot is running! Find it on Telegram and press /start")
    try:
        app.run_polling(allowed_updates=None, drop_pending_updates=True)
    except KeyboardInterrupt:
        print("Bot stopped")

if __name__ == "__main__":
    main()
