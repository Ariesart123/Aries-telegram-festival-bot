import time, threading, schedule, requests, sqlite3, io
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# ================= CONFIG =================
BOT_TOKEN = "8163939058:AAHi-1Md5aWgRTj_XjlCsdIf8MVTBxgEB38"
GEMINI_API_KEY = "AIzaSyDmvNpmngQbzZjT4eXUyXw7uAd0UnO1ygg"
CALENDARIFIC_API_KEY = "txouJTuJpPsrYttzXEJovNa6hBn04yuk"

FOOTER = "\n\n𝐼 𝑎𝑚 𝑦𝑜𝑢𝑟 @arieseditz"

genai.configure(api_key=GEMINI_API_KEY)

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
    "01-01": "New Year",
    "26-01": "Republic Day",
    "15-08": "Independence Day",
    "02-10": "Gandhi Jayanti",
    "25-12": "Christmas"
}

def detect_today_festival():
    now = datetime.now()
    key = now.strftime("%d-%m")

    # Fixed
    if key in FIXED_FESTIVALS:
        return FIXED_FESTIVALS[key]

    # Calendarific (dynamic festivals)
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
            return holidays[0]["name"]
    except:
        pass

    # Wikipedia fallback
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/holidays/{now.month}/{now.day}",
            timeout=5
        ).json()
        if r.get("holidays"):
            return r["holidays"][0]["text"]
    except:
        pass

    return None

# ================= TODAY TEXT =================
def get_today_text():
    now = datetime.now()
    date_str = now.strftime("%d %B")
    lines = []

    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}",
            timeout=5
        ).json()
        for e in r.get("events", [])[:3]:
            lines.append(f"• {e['year']} – {e['text']}")
    except:
        pass

    try:
        fact = requests.get(
            f"http://numbersapi.com/{now.month}/{now.day}/date",
            timeout=5
        ).text
        lines.append(f"• {fact}")
    except:
        pass

    if len(lines) < 2:
        try:
            model = genai.GenerativeModel("gemini-pro")
            res = model.generate_content(
                f"List 2 real historical events that happened on {date_str}. "
                f"Facts only. English only."
            )
            for l in res.text.split("\n"):
                if l.strip():
                    lines.append(f"• {l.strip('-• ')}")
        except:
            pass

    return f"✨ What's Special Today – {date_str}\n\n" + "\n".join(lines) + FOOTER

# ================= GLOW TEXT =================
def draw_glow(draw, pos, text, font):
    for s in range(8, 0, -2):
        draw.text(pos, text, fill=(255,215,120),
                  font=font, anchor="mm",
                  stroke_width=s, stroke_fill=(255,215,120))
    draw.text(pos, text, fill="white", font=font, anchor="mm")

# ================= ANIMATED GIF =================
def generate_gif(date_str, title):
    W, H = 1280, 720
    frames = []

    try:
        title_f = ImageFont.truetype("arial.ttf", 76)
        sub_f = ImageFont.truetype("arial.ttf", 36)
        brand_f = ImageFont.truetype("arial.ttf", 28)
    except:
        title_f = sub_f = brand_f = ImageFont.load_default()

    for shift in range(0, 120, 4):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)

        for y in range(H):
            d.line(
                (0, y, W, y),
                fill=((30+shift+y)%255, (50+y//2)%255, (90+shift*2)%255)
            )

        overlay = Image.new("RGBA", (W, H), (0,0,0,140))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        d = ImageDraw.Draw(img)

        draw_glow(d, (W//2, H//2 - 60), title, title_f)
        d.text((W//2, H//2 + 20), date_str,
               fill=(220,220,220), font=sub_f, anchor="mm")

        d.text((W-20, H-20), "𝐴𝑟𝑖𝑒𝑠 𝐸𝑑𝑖𝑡𝑧",
               fill=(200,200,200), font=brand_f, anchor="rd")

        frames.append(img.convert("RGB"))

    out = io.BytesIO()
    frames[0].save(out, format="GIF",
                   append_images=frames[1:],
                   save_all=True, duration=90, loop=0)
    out.seek(0)
    return out

# ================= COMMANDS =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")

    if festival:
        gif = generate_gif(date_str, f"HAPPY {festival.upper()}")
    else:
        gif = generate_gif(date_str, "WHAT'S SPECIAL TODAY?")

    text = get_today_text()
    await update.message.reply_animation(animation=gif, caption=text)

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (gid,))
    db.commit()
    await update.message.reply_text("✅ Group registered." + FOOTER)

# ================= AUTO MORNING =================
def auto_morning(app):
    festival = detect_today_festival()
    date_str = datetime.now().strftime("%d %B")

    title = f"HAPPY {festival.upper()}" if festival else "WHAT'S SPECIAL TODAY?"
    gif = generate_gif(date_str, title)
    text = get_today_text()

    for gid in get_groups():
        try:
            app.bot.send_animation(gid, gif, caption=text)
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

    print("🤖 Bot running – auto festival detection enabled")
    app.run_polling()

if __name__ == "__main__":
    main()
