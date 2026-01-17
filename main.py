import time
import threading
import schedule
import requests
import sqlite3
import io
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
CALENDARIFIC_API_KEY = "txouJTuJpPsrYttzXEJovNa6hBn04yuk"

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS groups (gid INTEGER PRIMARY KEY)")
db.commit()

def get_groups():
    cur.execute("SELECT gid FROM groups")
    return [x[0] for x in cur.fetchall()]

# ================= FESTIVAL DETECTION =================
FIXED_FESTIVALS = {
    "01-01": "NEW YEAR",
    "26-01": "REPUBLIC DAY",
    "15-08": "INDEPENDENCE DAY",
    "02-10": "GANDHI JAYANTI",
    "25-12": "CHRISTMAS",
}

def detect_today_festival():
    now = datetime.now()
    key = now.strftime("%d-%m")

    if key in FIXED_FESTIVALS:
        return FIXED_FESTIVALS[key]

    try:
        url = (
            "https://calendarific.com/api/v2/holidays"
            f"?api_key={CALENDARIFIC_API_KEY}"
            f"&country=IN&year={now.year}"
            f"&month={now.month}&day={now.day}"
        )
        data = requests.get(url, timeout=6).json()
        holidays = data.get("response", {}).get("holidays", [])
        if holidays:
            return holidays[0]["name"].upper()
    except:
        pass

    return None

# ================= IMAGE GENERATOR (FIXED) =================
def generate_image(date_str, title):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (15, 15, 25))
    d = ImageDraw.Draw(img)

    # Smooth gradient background (NO STRIPS)
    top = (30, 40, 80)
    bottom = (8, 8, 15)

    for y in range(H):
        r = int(top[0] + (bottom[0] - top[0]) * (y / H))
        g = int(top[1] + (bottom[1] - top[1]) * (y / H))
        b = int(top[2] + (bottom[2] - top[2]) * (y / H))
        d.line((0, y, W, y), fill=(r, g, b))

    # Center focus panel
    panel = Image.new("RGBA", (W - 200, 220), (0, 0, 0, 160))
    img.paste(panel, (100, H // 2 - 110), panel)
    d = ImageDraw.Draw(img)

    try:
        title_f = ImageFont.truetype("arial.ttf", 88)
        date_f = ImageFont.truetype("arial.ttf", 40)
        brand_f = ImageFont.truetype("arial.ttf", 28)
    except:
        title_f = date_f = brand_f = ImageFont.load_default()

    # Strong glowing title
    for s in range(10, 0, -2):
        d.text(
            (W // 2, H // 2 - 30),
            title,
            font=title_f,
            anchor="mm",
            fill=(255, 190, 120),
            stroke_width=s,
            stroke_fill=(255, 190, 120),
        )

    d.text(
        (W // 2, H // 2 - 30),
        title,
        font=title_f,
        anchor="mm",
        fill="white",
    )

    # Date
    d.text(
        (W // 2, H // 2 + 45),
        date_str,
        font=date_f,
        anchor="mm",
        fill=(210, 210, 210),
    )

    # Branding (inside image)
    d.text(
        (W - 30, H - 30),
        "𝐴𝑟𝑖𝑒𝑠 𝐸𝑑𝑖𝑡𝑧",
        font=brand_f,
        anchor="rd",
        fill=(180, 180, 180),
    )

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=95)
    out.seek(0)
    return out

# ================= COMMAND =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")
    title = f"HAPPY {festival}" if festival else "WHAT'S SPECIAL TODAY?"
    image = generate_image(date_str, title)

    # IMAGE ONLY (NO TEXT, NO CAPTION)
    await update.message.reply_photo(photo=image)

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()

# ================= AUTO MORNING =================
def auto_morning(app):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")
    title = f"HAPPY {festival}" if festival else "WHAT'S SPECIAL TODAY?"
    image = generate_image(date_str, title)

    for gid in get_groups():
        try:
            app.bot.send_photo(gid, photo=image)
        except:
            pass

def scheduler(app):
    schedule.every().day.at("07:00").do(lambda: auto_morning(app))
    while True:
        schedule.run_pending()
        time.sleep(1)

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("addgroup", addgroup))

    threading.Thread(target=scheduler, args=(app,), daemon=True).start()

    print("🤖 Bot running — IMAGE ONLY, FIXED DESIGN")
    app.run_polling()

if __name__ == "__main__":
    main()
