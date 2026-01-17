import time
import random
import requests
import schedule
import threading
from datetime import datetime

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GROUP_ID = -1002253293244   # ❗ apna real group id yahan daalo

CALENDARIFIC_API_KEY = "txouJTuJpPsrYttzXEJovNa6hBn04yuk"
UNSPLASH_ACCESS_KEY = "pIKbVM-SvDSqZZOJh1jVfzXS7QI2WsQB-3TzJOyQ4v4"
COUNTRY = "IN"

bot = Bot(token=BOT_TOKEN)

# ================= FACT SYSTEM (HYBRID) =================
OFFLINE_FACTS = [
    "🧠 Did you know? Honey never spoils and can last thousands of years.",
    "🌍 Did you know? Earth is the only planet not named after a god.",
    "🚀 Did you know? A day on Venus is longer than a year on Venus.",
    "🦈 Did you know? Sharks existed before trees.",
    "💡 Did you know? The human brain uses about 20% of the body’s energy."
]

def get_fresh_fact():
    try:
        r = requests.get(
            "https://uselessfacts.jsph.pl/random.json?language=en",
            timeout=5
        )
        if r.status_code == 200:
            return "🧠 Did you know? " + r.json().get("text")
    except:
        pass
    return random.choice(OFFLINE_FACTS)

# ================= AUTO FACTS =================
def send_morning_fact():
    bot.send_message(
        chat_id=GROUP_ID,
        text=f"🌅 *Good Morning!*\n\n{get_fresh_fact()}",
        parse_mode="Markdown"
    )

def send_evening_fact():
    bot.send_message(
        chat_id=GROUP_ID,
        text=f"🌙 *Good Evening!*\n\n{get_fresh_fact()}",
        parse_mode="Markdown"
    )

# ================= WEEKLY SUMMARY =================
def send_weekly_summary():
    text = (
        "📊 *Weekly Summary*\n\n"
        "• 🌅 Daily morning facts\n"
        "• 🌙 Daily evening facts\n"
        "• 🎉 Festival wishes & images\n"
        "• 📜 History & knowledge updates\n\n"
        "Stay curious & keep learning! 🚀"
    )
    bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="Markdown")

# ================= FESTIVALS =================
def get_festival_image(name):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": name + " india festival",
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 1
    }
    data = requests.get(url, params=params).json()
    if data.get("results"):
        return data["results"][0]["urls"]["regular"]
    return None

def get_wikipedia_details(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    data = requests.get(url).json()
    return data.get("extract")

def check_festivals():
    today = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().year

    url = (
        f"https://calendarific.com/api/v2/holidays?"
        f"api_key={CALENDARIFIC_API_KEY}&country={COUNTRY}&year={year}"
    )

    data = requests.get(url).json()

    for holiday in data["response"]["holidays"]:
        if holiday["date"]["iso"] == today:
            image = get_festival_image(holiday["name"])
            details = get_wikipedia_details(holiday["name"])

            if image:
                bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=image,
                    caption=f"🎉 {holiday['name']}"
                )
            else:
                bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"🎉 {holiday['name']}"
                )

            if details:
                bot.send_message(chat_id=GROUP_ID, text=details)

# ================= COMMANDS =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    date_str = now.strftime("%d %B")

    url = (
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/"
        f"{now.month}/{now.day}"
    )
    data = requests.get(url).json()
    event = data["events"][0]["text"] if data.get("events") else "No major event found."

    await update.message.reply_text(
        f"📅 *Today: {date_str}*\n\n"
        f"📜 *On this day in history:*\n{event}",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Telegram Festival & Knowledge Bot*\n\n"
        "*Commands:*\n"
        "/today – On this day in history\n"
        "/help – How to use the bot\n\n"
        "*Automatic Features:*\n"
        "🌅 Morning facts\n"
        "🌙 Evening facts\n"
        "🎉 Festival wishes with images\n"
        "📜 History details\n"
        "📊 Weekly summary\n\n"
        "Bot runs automatically 24/7."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= SCHEDULER =================
def run_scheduler():
    schedule.every().day.at("07:00").do(send_morning_fact)
    schedule.every().day.at("19:00").do(send_evening_fact)
    schedule.every().day.at("08:00").do(check_festivals)
    schedule.every().sunday.at("20:00").do(send_weekly_summary)

    while True:
        schedule.run_pending()
        time.sleep(1)

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("help", help_cmd))

    threading.Thread(target=run_scheduler, daemon=True).start()

    print("🤖 Bot is running (FINAL, v22.5 compatible)")
    app.run_polling()

if __name__ == "__main__":
    main()
