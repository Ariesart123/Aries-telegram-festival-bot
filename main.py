import time
import random
import requests
import schedule
import threading
import sqlite3
from datetime import datetime, timedelta

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

import google.generativeai as genai

# ================== CONFIG ==================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GEMINI_API_KEY = "AIzaSyDmvNpmngQbzZjT4eXUyXw7uAd0UnO1ygg"

ADMIN_IDS = [7305616798]  # ❗ apna Telegram user ID yahan daalo
COUNTRY = "IN"

# ================== INIT ==================
bot = Bot(token=BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# ================== DATABASE ==================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)")
cur.execute(
    "CREATE TABLE IF NOT EXISTS usage (command TEXT PRIMARY KEY, count INTEGER)"
)
db.commit()

def track(cmd):
    cur.execute(
        "INSERT INTO usage VALUES (?,1) "
        "ON CONFLICT(command) DO UPDATE SET count=count+1",
        (cmd,)
    )
    db.commit()

def all_groups():
    cur.execute("SELECT group_id FROM groups")
    return [g[0] for g in cur.fetchall()]

# ================== AI ==================
def ai_text(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        r = model.generate_content(prompt)
        return r.text.strip()
    except:
        return None

# ================== FACTS ==================
FACTS = [
    "🧠 Honey never spoils.",
    "🌍 Earth is not perfectly round.",
    "🚀 Space is completely silent.",
    "🦈 Sharks existed before trees."
]

def random_fact():
    return random.choice(FACTS)

# ================== HISTORY (MULTI-SOURCE) ==================
IMPORTANT_HISTORY = {
    "26-01": {
        "en": "India celebrates Republic Day, marking the adoption of the Constitution in 1950.",
        "hi": "भारत आज गणतंत्र दिवस मनाता है, जब 1950 में संविधान लागू हुआ।"
    },
    "15-08": {
        "en": "India celebrates Independence Day, gaining freedom from British rule in 1947.",
        "hi": "भारत आज स्वतंत्रता दिवस मनाता है, 1947 में आज़ादी मिली।"
    },
    "02-10": {
        "en": "Birth anniversary of Mahatma Gandhi, the Father of the Nation.",
        "hi": "महात्मा गांधी जयंती, राष्ट्रपिता की जन्मतिथि।"
    }
}

def get_today_history():
    now = datetime.now()
    key = now.strftime("%d-%m")

    # 1) Wikipedia
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("events"):
                return random.choice(data["events"])["text"], None
    except:
        pass

    # 2) Numbers API
    try:
        num = requests.get(
            f"http://numbersapi.com/{now.month}/{now.day}/date",
            timeout=5
        )
        if num.status_code == 200 and num.text:
            return num.text, None
    except:
        pass

    # 3) Offline India
    if key in IMPORTANT_HISTORY:
        return IMPORTANT_HISTORY[key]["en"], IMPORTANT_HISTORY[key]["hi"]

    # 4) AI fallback
    ai = ai_text(
        f"Explain why {now.strftime('%d %B')} is important in Indian history in 2 lines (English + Hindi)."
    )
    if ai:
        return ai, None

    return (
        "Today is a good day to reflect on history and learn something new.",
        "आज इतिहास से कुछ नया सीखने और आगे बढ़ने का अच्छा दिन है।"
    )

# ================== COMMANDS ==================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track("help")
    await update.message.reply_text(
        "🤖 *Festival & Knowledge Bot*\n\n"
        "/today – Today in history (EN + HI)\n"
        "/tomorrow – Tomorrow preview\n"
        "/thisweek – Weekly history summary\n"
        "/broadcast – Admin message\n"
        "/stats – Admin analytics\n"
        "/addgroup – Add group (admin)\n"
        "/help – Help",
        parse_mode="Markdown"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track("today")
    en, hi = get_today_history()
    date_str = datetime.now().strftime("%d %B")

    if not hi:
        hi = "आज के दिन इतिहास में कई महत्वपूर्ण घटनाएँ हुई थीं।"

    await update.message.reply_text(
        f"📅 *Today: {date_str}*\n\n"
        f"📜 {en}\n\n"
        f"🇮🇳 {hi}",
        parse_mode="Markdown"
    )

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track("tomorrow")
    t = datetime.now() + timedelta(days=1)
    await update.message.reply_text(
        f"🔮 *Tomorrow: {t.strftime('%d %B')}*\n\n"
        "Every day shapes history.\n\n"
        "🇮🇳 हर दिन इतिहास बनता है।",
        parse_mode="Markdown"
    )

async def thisweek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track("thisweek")
    await update.message.reply_text(
        "📊 *This Week in History*\n\n"
        "This week witnessed important moments across politics, science and culture.\n\n"
        "🇮🇳 इस सप्ताह इतिहास में कई महत्वपूर्ण घटनाएँ हुईं।",
        parse_mode="Markdown"
    )

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()
    await update.message.reply_text("✅ Group added permanently.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    track("broadcast")
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: /broadcast message")
        return
    for gid in all_groups():
        try:
            bot.send_message(gid, f"📢 *Admin Message*\n\n{msg}", parse_mode="Markdown")
        except:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    cur.execute("SELECT command, count FROM usage")
    rows = cur.fetchall()
    text = "📊 *Bot Usage Stats*\n\n"
    for c, n in rows:
        text += f"/{c} → {n}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================== AUTO SCHEDULER ==================
def morning_history():
    en, hi = get_today_history()
    for gid in all_groups():
        try:
            bot.send_message(
                gid,
                f"🌅 *Morning History*\n\n{en}\n\n🇮🇳 {hi}",
                parse_mode="Markdown"
            )
        except:
            pass

def evening_fact():
    for gid in all_groups():
        try:
            bot.send_message(
                gid,
                f"🌙 *Evening Fact*\n\n{random_fact()}",
                parse_mode="Markdown"
            )
        except:
            pass

def scheduler():
    schedule.every().day.at("07:00").do(morning_history)
    schedule.every().day.at("19:00").do(evening_fact)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("thisweek", thisweek))
    app.add_handler(CommandHandler("addgroup", addgroup))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))

    threading.Thread(target=scheduler, daemon=True).start()

    print("🤖 Bot running with Gemini AI + Database")
    app.run_polling()

if __name__ == "__main__":
    main()
