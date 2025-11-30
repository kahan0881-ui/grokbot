#!/usr/bin/env python3
import os, json, time, asyncio, logging, aiohttp
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN = int(os.getenv("ADMIN_ID", "0"))
MODEL = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4.1-fast:free")
REFERER = os.getenv("HTTP_REFERER", "https://replit.com")

FB_LINK = "https://www.facebook.com/share/176uqLSYkX/"
TG_GROUP = "https://t.me/techirfantips"
YT_CHANNEL = "https://youtube.com/@paksauditech?si=YBeaMMb7N3ILPkQs"

DATA_FILE = Path("joined.json")
LOG_FILE = Path("bot.log")
RATE_LIMIT = 2
last_msg = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(level)s %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])

def load_data(): return json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
def save_data(d): DATA_FILE.write_text(json.dumps(d, indent=2))
joined = load_data()

async def check_tg(user_id, context):
    try:
        member = await context.bot.get_chat_member("@techirfantips", user_id)
        if member.status in ["member", "administrator", "creator"]:
            joined[str(user_id)] = True
            save_data(joined)
            return True
    except: pass
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if str(uid) in joined or uid == ADMIN:
        await update.message.reply_text("Walaikum Salam bhai! Ab poocho jo poochna hai 😊")
        return

    keyboard = [
        [InlineKeyboardButton("Follow Facebook", url=FB_LINK)],
        [InlineKeyboardButton("Join Telegram Group", url=TG_GROUP)],
        [InlineKeyboardButton("Subscribe YouTube @paksauditech", url=YT_CHANNEL)],
        [InlineKeyboardButton("✅ Sab Kar Diya – Check Karo", callback_data="check")]
    ]
    await update.message.reply_text(
        "🤖 Bot use karne se pehle ye teeno zaruri hain:\n\n"
        "1️⃣ Facebook follow karo\n"
        "2️⃣ Telegram group join karo\n"
        "3️⃣ YouTube channel subscribe karo → @paksauditech\n\n"
        "Sab karne ke baad neeche wala button daba do → bot khud on ho jayega!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "check":
        if await check_tg(q.from_user.id, context) or q.from_user.id == ADMIN:
            await q.edit_message_text("🎉 Mubarak ho! Teeno kaam poore!\nAb bot full use kar sakte ho")
        else:
            await q.edit_message_text("❌ Abhi tak Telegram group join nahi kiya!\nPehle join karo phir button dabao")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if str(uid) not in joined and uid != ADMIN:
        await start(update, context)
        return

    now = time.time()
    if uid in last_msg and now - last_msg[uid] < RATE_LIMIT:
        await update.message.reply_text("Thori der wait karo bhai 😅")
        return
    last_msg[uid] = now

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.post("https://openrouter.ai/api/v1/chat/completions",
                json={"model": MODEL, "messages": [
                    {"role": "system", "content": "Reply only in Roman Urdu using Latin script. Keep it short, natural and friendly."},
                    {"role": "user", "content": update.message.text}
                ]},
                headers={"Authorization": f"Bearer {API_KEY}", "Referer": REFERER}) as r:
                reply = (await r.json())["choices"][0]["message"]["content"] if r.status == 200 else "Server masla hai thori der baad try karo"
    except:
        reply = "Network issue hai bhai, thori der mein try karna"
    await update.message.reply_text(reply)

# Admin Commands (sirf tum use kar sakte ho)
async def grant(update: Update, context): 
    if update.effective_user.id != ADMIN: return
    try: uid = int(context.args[0]); joined[str(uid)] = True; save_data(joined); await update.message.reply_text(f"Granted { uid }")
    except: await update.message.reply_text("Galat: /grant 123456789")

async def stats(update: Update, context):
    if update.effective_user.id != ADMIN: return
    await update.message.reply_text(f"Total allowed users: {len(joined)}")

def main():
    print("BOT STARTED – Facebook + Telegram + YouTube @paksauditech Mandatory")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    app.add_handler(CommandHandler("grant", grant))
    app.add_handler(CommandHandler("stats", stats))
    app.run_polling()

if __name__ == "__main__":
    main()
  
