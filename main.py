import time
import random
import requests
import schedule
import threading
from datetime import datetime

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========= CONFIG =========
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GROUP_ID = -1002253293244   # apna group id yahan daalo

CALENDARIFIC_API_KEY = "txouJTuJpPsrYttzXEJovNa6hBn04yuk"
UNSPLASH_ACCESS_KEY = "pIKbVM-SvDSqZZOJh1jVfzXS7QI2WsQB-3TzJOyQ4v4"
COUNTRY = "IN"

bot = Bot(token=BOT_TOKEN)

# ========= FACTS =========
FACTS = [
    "🧠 Did you know? Honey never spoils.",
    "🌍 Did you know? Earth is not perfectly round.",
    "🚀 Did you know? Space is completely silent.",
    "🦈 Did you know? Sharks existed before trees.",
]

def random_fact():
    return random.choice(FACTS)

# ========= AUTO MESSAGES =========
def morning_fact():
    bot.send_message(GROUP_ID, f"🌅 Good Morning!\n\n{random_fact()}")

def evening_fact():
    bot.send_message(GROUP_ID, f"🌙 Good Evening!\n\n{random_fact()}")

# ========= FESTIVAL CHECK =========
def check_festival():
    today = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().year

    url = f"https://calendarific.com/api/v2/holidays?api_key={CALENDARIFIC_API_KEY}&country=IN&year={year}"

    try:
        data = requests.get(url, timeout=10).json()
        for h in data["response"]["holidays"]:
            if h["date"]["iso"] == today:
                bot.send_message(GROUP_ID, f"🎉 {h['name']}")
    except:
        pass

# ========= COMMANDS =========
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Telegram Festival & Knowledge Bot\n\n"
        "/today – On this day in history\n"
        "/help – Bot usage\n\n"
        "Auto: Morning facts, Evening facts, Festivals, Weekly summary"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    date_str = now.strftime("%d %B")

    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        event = data["events"][0]["text"]
    except:
        event = "No historical data available today."

    await update.message.reply_text(
        f"📅 Today: {date_str}\n\n📜 On this day in history:\n{event}"
    )

# ========= SCHEDULER =========
def scheduler():
    schedule.every().day.at("07:00").do(morning_fact)
    schedule.every().day.at("19:00").do(evening_fact)
    schedule.every().day.at("08:00").do(check_festival)

    while True:
        schedule.run_pending()
        time.sleep(1)

# ========= MAIN =========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today))

    threading.Thread(target=scheduler, daemon=True).start()

    print("🤖 Bot running safely")
    app.run_polling()

if __name__ == "__main__":
    main()
