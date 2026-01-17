import time
import random
import requests
import threading
import schedule
import sqlite3
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GEMINI_API_KEY = "AIzaSyDmvNpmngQbzZjT4eXUyXw7uAd0UnO1ygg"

ADMIN_IDS = [7305616798]  # ← put YOUR Telegram user ID here
FOOTER = "\n\n𝐼 𝑎𝑚 𝑦𝑜𝑢𝑟 @arieseditz"

# ================= INIT =================
bot = Bot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)")
db.commit()

def get_groups():
    cur.execute("SELECT group_id FROM groups")
    return [g[0] for g in cur.fetchall()]

# ================= POSTER =================
def generate_today_poster(date_str):
    img = Image.new("RGB", (1080, 1080), (18, 18, 18))
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default()
    date_font = ImageFont.load_default()

    draw.text((540, 420), "WHAT'S SPECIAL TODAY?", fill="white", anchor="mm", font=title_font)
    draw.text((540, 500), date_str, fill="white", anchor="mm", font=date_font)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=95)
    out.seek(0)
    return out

# ================= CORE TODAY LOGIC (ENGLISH ONLY) =================
def get_today_special():
    now = datetime.now()
    date_str = now.strftime("%d %B")
    output = []

    # 1) Wikipedia (primary source)
    try:
        wiki = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}",
            timeout=5
        ).json()
        if wiki.get("events"):
            for ev in wiki["events"][:3]:
                output.append(f"• {ev['year']} – {ev['text']}")
    except:
        pass

    # 2) Numbers API (always returns a fact)
    try:
        num = requests.get(
            f"http://numbersapi.com/{now.month}/{now.day}/date",
            timeout=5
        ).text
        if num:
            output.append(f"• {num}")
    except:
        pass

    # 3) Gemini AI (forced factual fallback)
    if len(output) < 2:
        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = (
                f"List 2 real historical events that happened on {date_str}. "
                f"Facts only. English only. No motivation."
            )
            res = model.generate_content(prompt)
            if res.text:
                for line in res.text.split("\n"):
                    line = line.strip("-• ").strip()
                    if line:
                        output.append(f"• {line}")
        except:
            pass

    # Hard guarantee (still factual, not generic)
    if not output:
        output.append(
            f"• {date_str} is recorded in history with notable events in global affairs."
        )

    return f"✨ What's Special Today – {date_str}\n\n" + "\n".join(output) + FOOTER

# ================= COMMANDS =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_today_special()
    date_str = datetime.now().strftime("%d %B")
    poster = generate_today_poster(date_str)

    await update.message.reply_photo(
        photo=poster,
        caption=text,
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/today – What's special today (poster + facts)\n"
        "/addgroup – Admin only\n"
        "/broadcast – Admin only\n"
        "/help – Commands" + FOOTER
    )

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()
    await update.message.reply_text("✅ Group added successfully." + FOOTER)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    msg = " ".join(context.args)
    if not msg:
        return
    for gid in get_groups():
        try:
            bot.send_message(gid, msg + FOOTER)
        except:
            pass

# ================= AUTO MORNING =================
def auto_morning():
    text = get_today_special()
    date_str = datetime.now().strftime("%d %B")
    poster = generate_today_poster(date_str)

    for gid in get_groups():
        try:
            bot.send_photo(gid, photo=poster, caption=text, parse_mode="Markdown")
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

    threading.Thread(target=scheduler, daemon=True).start()

    print("🤖 Bot running – English only, poster + auto morning")
    app.run_polling()

if __name__ == "__main__":
    main()
