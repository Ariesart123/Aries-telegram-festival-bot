import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
NUMBERS_API = "http://numbersapi.com"
WATERMARK = "Aries Editz"
OUTPUT_DIR = "images"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# =========================================


def get_today_facts():
    today = datetime.now()
    month = today.month
    day = today.day

    facts = []

    # Numbers API – history
    try:
        r = requests.get(f"{NUMBERS_API}/{month}/{day}/date", timeout=10)
        if r.status_code == 200 and r.text:
            facts.append(r.text)
    except:
        pass

    # Always fallback facts (never empty)
    if not facts:
        facts = [
            "Important historical events happened on this day.",
            "This day has witnessed major moments in world history.",
            "A remarkable day remembered across generations."
        ]

    return facts, today.strftime("%d %B")


def generate_hd_image(date_text, facts):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), "#000000")
    d = ImageDraw.Draw(img)

    # -------- Smooth Gradient Background --------
    for y in range(H):
        r = int(20 + (y / H) * 40)
        g = int(30 + (y / H) * 70)
        b = int(60 + (y / H) * 110)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    # -------- Fonts --------
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 90)
        date_font = ImageFont.truetype("arial.ttf", 42)
        info_font = ImageFont.truetype("arial.ttf", 38)
        watermark_font = ImageFont.truetype("arialbd.ttf", 36)
    except:
        title_font = ImageFont.load_default()
        date_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        watermark_font = ImageFont.load_default()

    # -------- Title --------
    d.text(
        (W // 2, 180),
        "WHAT'S SPECIAL TODAY?",
        fill=(255, 255, 255),
        font=title_font,
        anchor="mm"
    )

    # -------- Date --------
    d.text(
        (W // 2, 280),
        date_text,
        fill=(220, 220, 220),
        font=date_font,
        anchor="mm"
    )

    # -------- Facts --------
    y = 420
    for fact in facts[:3]:
        wrapped = text_wrap(fact, info_font, W - 300)
        for line in wrapped:
            d.text((W // 2, y), line, fill=(245, 245, 245), font=info_font, anchor="mm")
            y += 50
        y += 20

    # -------- Watermark --------
    d.text(
        (W - 40, H - 30),
        WATERMARK,
        fill=(200, 200, 200),
        font=watermark_font,
        anchor="rs"
    )

    path = f"{OUTPUT_DIR}/today_hd.jpg"
    img.save(path, quality=95, subsampling=0)
    return path


def text_wrap(text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + word + " "
        w, h = font.getsize(test)
        if w <= max_width:
            current = test
        else:
            lines.append(current.strip())
            current = word + " "
    lines.append(current.strip())
    return lines


# ================= COMMAND =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts, date_text = get_today_facts()
    image_path = generate_hd_image(date_text, facts)

    await update.message.reply_photo(photo=open(image_path, "rb"))


# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    print("🤖 Bot running safely")
    app.run_polling()


if __name__ == "__main__":
    main()
