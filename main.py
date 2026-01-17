import time
import random
import requests
import threading
import schedule
import sqlite3
from datetime import datetime, timedelta

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

import google.generativeai as genai

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GEMINI_API_KEY = "AIzaSyDmvNpmngQbzZjT4eXUyXw7uAd0UnO1ygg"

ADMIN_IDS = [7305616798]  # 🔴 apna Telegram user ID daalo
COUNTRY = "IN"

# ================= INIT =================
bot = Bot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS usage (command TEXT PRIMARY KEY, count INTEGER)")
db.commit()

def track(cmd):
    cur.execute(
        "INSERT INTO usage VALUES (?,1) "
        "ON CONFLICT(command) DO UPDATE SET count=count+1",
        (cmd,)
    )
    db.commit()

def get_groups():
    cur.execute("SELECT group_id FROM groups")
    return [g[0] for g in cur.fetchall()]

# ================= OFFLINE INDIA DAYS =================
INDIA_DAYS = {
    "26-01": ("Republic Day of India", "भारत का गणतंत्र दिवस"),
    "15-08": ("Independence Day of India", "भारत का स्वतंत्रता दिवस"),
    "02-10": ("Gandhi Jayanti", "गांधी जयंती"),
    "14-04": ("Dr. B. R. Ambedkar Jayanti", "डॉ. भीमराव अंबेडकर जयंती"),
    "01-05": ("Labour Day", "मजदूर दिवस"),
}

# ================= GEMINI =================
def ai_force_today(date_str):
    prompt = (
        f"Explain what is special about {date_str} "
        f"using real history, culture, world events or observances. "
        f"Give short, factual explanation in English and Hindi. "
        f"Do NOT use generic motivational lines."
    )
    try:
        model = genai.GenerativeModel("gemini-pro")
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return None

# ================= CORE TODAY LOGIC =================
def get_today_special():
    now = datetime.now()
    key = now.strftime("%d-%m")
    date_str = now.strftime("%d %B")

    output = []

    # 1️⃣ INDIA SPECIAL DAY
    if key in INDIA_DAYS:
        en, hi = INDIA_DAYS[key]
        output.append(f"🇮🇳 *Special Day in India:*\n{en}\n{hi}")

    # 2️⃣ WIKIPEDIA EVENT
    try:
        wiki = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}",
            timeout=5
        ).json()
        if wiki.get("events"):
            ev = random.choice(wiki["events"])
            output.append(f"📜 *Historical Event:*\n{ev['year']} – {ev['text']}")
    except:
        pass

    # 3️⃣ NUMBERS API (ALWAYS RETURNS)
    try:
        num = requests.get(
            f"http://numbersapi.com/{now.month}/{now.day}/date",
            timeout=5
        ).text
        if num:
            output.append(f"🧠 *Did you know?*\n{num}")
    except:
        pass

    # 4️⃣ GEMINI FORCE (NO EMPTY ALLOWED)
    if len(output) < 2:
        ai = ai_force_today(date_str)
        if ai:
            output.append(f"✨ *Why Today Is Special:*\n{ai}")

    # FINAL GUARANTEE
    if not output:
        output.append(
            "📜 *On this day:*\n"
            "This date is associated with important historical events "
            "and cultural developments across the world.\n\n"
            "आज का दिन इतिहास और वैश्विक घटनाओं से जुड़ा हुआ है।"
        )

    return f"✨ *What's Special Today – {date_str}*\n\n" + "\n\n".join(output)

# ================= COMMANDS =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track("today")
    text = get_today_special()
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/today – What's special today\n"
        "/tomorrow – Tomorrow preview\n"
        "/thisweek – Weekly summary\n"
        "/addgroup – Admin only\n"
        "/broadcast – Admin message\n"
        "/stats – Bot usage"
    )

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()
    await update.message.reply_text("✅ Group added successfully")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    msg = " ".join(context.args)
    if not msg:
        return
    for gid in get_groups():
        try:
            bot.send_message(gid, msg)
        except:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    cur.execute("SELECT command, count FROM usage")
    rows = cur.fetchall()
    text = "📊 Usage Stats\n\n"
    for c, n in rows:
        text += f"/{c} → {n}\n"
    await update.message.reply_text(text)

# ================= AUTO MORNING =================
def auto_morning():
    text = get_today_special()
    for gid in get_groups():
        try:
            bot.send_message(gid, text, parse_mode="Markdown")
        except:
            pass

def scheduler():
    schedule.every().day.at("07:00").do(auto_morning)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("addgroup", addgroup))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))

    threading.Thread(target=scheduler, daemon=True).start()

    print("🤖 Bot running – /today is guaranteed informative")
    app.run_polling()

if __name__ == "__main__":
    main()
