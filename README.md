# Sleep Tracker Bot 🌙

A Telegram bot to track your sleep sessions and get insights to improve your quality of life.

## Features

- 😴 Log sleep sessions (bedtime, wake time, quality)
- 📊 View statistics (average sleep duration, quality ratings)
- 💡 Get AI-powered insights based on your sleep patterns
- 🔗 Track correlations over time

## Setup

1. **Create a Telegram Bot**
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot and get your token

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure**
   - Copy `.env.example` to `.env`
   - Add your bot token: `TELEGRAM_BOT_TOKEN=your_token`

4. **Run**
   ```bash
   python bot.py
   ```

5. **Start using**
   - Search for your bot on Telegram
   - Press `/start`
   - Use the beautiful interface to track sleep!

## How It Works

- **Log Sleep**: Input bedtime, wake time, and quality rating
- **View Stats**: See your sleep patterns from the last 7 days
- **Get Insights**: Get personalized recommendations based on your data

## Technologies

- Python
- python-telegram-bot
- SQLite
