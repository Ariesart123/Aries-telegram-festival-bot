import schedule
import time
import random
import requests
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GROUP_ID = --1002253293244  # replace with your group id

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
        r = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
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
    summary = (
        "📊 *Weekly Summary*\n\n"
        "• 🌅 Daily morning facts\n"
        "• 🌙 Daily evening facts\n"
        "• 🎉 Festival wishes & images\n"
        "• 📜 History & knowledge updates\n\n"
        "Stay curious & keep learning! 🚀"
    )
    bot.send_message(chat_id=GROUP_ID, text=summary, parse_mode="Markdown")

# ================= FESTIVAL =================
def get_festival_image(festival_name):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": festival_name + " india festival",
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 1
    }
    r = requests.get(url, params=params).json()
    if r.get("results"):
        return r["results"][0]["urls"]["regular"]
    return None

def get_wikipedia_details(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    r = requests.get(url).json()
    return r.get("extract")

def send_festival(festival_name):
    image = get_festival_image(festival_name)
    details = get_wikipedia_details(festival_name)

    if image:
        bot.send_photo(chat_id=GROUP_ID, photo=image, caption=f"🎉 {festival_name}")
    else:
        bot.send_message(chat_id=GROUP_ID, text=f"🎉 {festival_name}")

    if details:
        bot.send_message(chat_id=GROUP_ID, text=details)

def check_lunar_festivals():
    year = datetime.now().year
    today_date = datetime.now().strftime("%Y-%m-%d")

    url = (
        f"https://calendarific.com/api/v2/holidays?"
        f"api_key={CALENDARIFIC_API_KEY}&country={COUNTRY}&year={year}"
    )

    data = requests.get(url).json()

    for holiday in data["response"]["holidays"]:
        if holiday["date"]["iso"] == today_date:
            send_festival(holiday["name"])

# ================= COMMANDS =================
def today(update, context):
    now = datetime.now()
    date_str = now.strftime("%d %B")

    wiki_url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}"
    data = requests.get(wiki_url).json()
    event = data["events"][0]["text"] if data.get("events") else "No major historical event found."

    message = (
        f"📅 *Today: {date_str}*\n\n"
        f"📜 *On this day in history:*\n"
        f"{event}"
    )
    update.message.reply_text(message, parse_mode="Markdown")

def help_cmd(update, context):
    help_text = (
        "🤖 *Telegram Festival & Knowledge Bot*\n\n"
        "*Commands:*\n"
        "/today – On this day in history\n"
        "/help – How to use this bot\n\n"
        "*Automatic Features:*\n"
        "🌅 Daily Morning Facts\n"
        "🌙 Daily Evening Facts\n"
        "🎉 Festival Wishes with Images\n"
        "📜 Festival & History Details\n"
        "📊 Weekly Summary (Sunday)\n\n"
        "This bot works automatically. No manual typing needed."
    )
    update.message.reply_text(help_text, parse_mode="Markdown")

# ================= SCHEDULER =================
schedule.every().day.at("07:00").do(send_morning_fact)
schedule.every().day.at("19:00").do(send_evening_fact)
schedule.every().day.at("08:00").do(check_lunar_festivals)
schedule.every().sunday.at("20:00").do(send_weekly_summary)

# ================= BOT START =================
updater = Updater(BOT_TOKEN)
dp = updater.dispatcher
dp.add_handler(CommandHandler("today", today))
dp.add_handler(CommandHandler("help", help_cmd))

updater.start_polling()
print("🤖 Bot running with /help command added...")

while True:
    schedule.run_pending()
    time.sleep(1)
