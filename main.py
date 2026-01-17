import time, threading, schedule, requests, sqlite3, io
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
    "25-12": "CHRISTMAS"
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
        r = requests.get(url, timeout=5).json()
        holidays = r.get("response", {}).get("holidays", [])
        if holidays:
            return holidays[0]["name"].upper()
    except:
        pass

    return None

# ================= GLOW TEXT =================
def draw_glow(draw, pos, text, font):
    for s in range(8, 0, -2):
        draw.text(
            pos, text,
            fill=(255, 200, 120),
            font=font,
            anchor="mm",
            stroke_width=s,
            stroke_fill=(255, 200, 120)
        )
    draw.text(pos, text, fill="white", font=font, anchor="mm")

# ================= ANIMATED GIF =================
def generate_gif(date_str, title):
    W, H = 1280, 720
    frames = []

    try:
        title_f = ImageFont.truetype("arial.ttf", 76)
        date_f = ImageFont.truetype("arial.ttf", 38)
        brand_f = ImageFont.truetype("arial.ttf", 30)
    except:
        title_f = date_f = brand_f = ImageFont.load_default()

    for shift in range(0, 120, 4):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)

        # Gradient background
        for y in range(H):
            d.line(
                (0, y, W, y),
                fill=((40+shift+y)%255, (50+y//2)%255, (90+shift*2)%255)
            )

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 140))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        d = ImageDraw.Draw(img)

        # Glowing title
        draw_glow(d, (W//2, H//2 - 50), title, title_f)

        # Date
        d.text(
            (W//2, H//2 + 30),
            date_str,
            fill=(220, 220, 220),
            font=date_f,
            anchor="mm"
        )

        # Branding
        d.text(
            (W-25, H-25),
            "𝐴𝑟𝑖𝑒𝑠 𝐸𝑑𝑖𝑡𝑧",
            fill=(200, 200, 200),
            font=brand_f,
            anchor="rd"
        )

        frames.append(img.convert("RGB"))

    out = io.BytesIO()
    frames[0].save(
        out,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=90,
        loop=0
    )
    out.seek(0)
    return out

# ================= COMMANDS =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")

    title = f"HAPPY {festival}" if festival else "WHAT'S SPECIAL TODAY?"
    gif = generate_gif(date_str, title)

    # ONLY GIF — NO TEXT, NO CAPTION
    await update.message.reply_animation(animation=gif)

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()

# ================= AUTO MORNING =================
def auto_morning(app):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")
    title = f"HAPPY {festival}" if festival else "WHAT'S SPECIAL TODAY?"
    gif = generate_gif(date_str, title)

    for gid in get_groups():
        try:
            app.bot.send_animation(gid, animation=gif)
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

    print("🤖 Bot running — GIF only, no text")
    app.run_polling()

if __name__ == "__main__":
    main()
