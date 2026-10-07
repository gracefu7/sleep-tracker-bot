import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)
CORS(app)

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
                    user_id TEXT,
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

@app.route('/')
def index():
    with open('app.html', 'r') as f:
        return f.read()

@app.route('/api/sleep', methods=['POST'])
def log_sleep():
    data = request.json
    db.add_sleep(
        data['user_id'],
        data['bedtime'],
        data['waketime'],
        data['quality'],
        data.get('notes', '')
    )
    return jsonify({"status": "ok"})

@app.route('/api/stats')
def get_stats():
    user_id = request.args.get('user_id')
    stats = db.get_stats(user_id, days=7)
    return jsonify({"stats": stats})

@app.route('/api/insights')
def get_insights():
    user_id = request.args.get('user_id')
    stats = db.get_stats(user_id, days=7)

    if not stats:
        return jsonify({"insights": '<p style="text-align:center;color:#999;">No data for insights yet</p>'})

    avg = stats["avg_duration"]
    quality = stats["avg_quality"]

    insights = '<div>'

    if avg < 6:
        insights += '<div class="insight">⚠️ You\'re getting less sleep than recommended (6-8h). Try to sleep earlier or improve your sleep environment.</div>'
    elif avg > 9:
        insights += '<div class="insight">📌 You\'re sleeping more than usual. Consider your daily activities and stress levels.</div>'
    else:
        insights += '<div class="insight">✅ Your sleep duration is healthy! Keep it up!</div>'

    if quality < 5:
        insights += '<div class="insight">😴 Your sleep quality is low. Tips: regular exercise, no screens 1h before bed, consistent schedule, cooler room temperature.</div>'
    elif quality > 8:
        insights += '<div class="insight">🌟 Excellent sleep quality! Your routine is working great. Keep it consistent!</div>'
    else:
        insights += '<div class="insight">👍 Your sleep quality is good. Small improvements in routine could make it even better.</div>'

    insights += f'<div class="insight">📈 Trend: {stats["count"]} sessions tracked. Keep logging to see more detailed patterns!</div>'
    insights += '</div>'

    return jsonify({"insights": insights})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)
