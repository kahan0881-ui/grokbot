#!/usr/bin/env python3
import os, json, time, asyncio, aiohttp
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MODEL = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4.1-fast:free")
REFERER = os.getenv("HTTP_REFERER", "https://replit.com")

# Links
FB_LINK = "https://www.facebook.com/share/176uqLSYkX/"
TG_GROUP = "https://t.me/techirfantips"
YT_CHANNEL = "https://youtube.com/@paksauditech"

# joined.json fix
DATA_FILE = Path("joined.json")
if not DATA_FILE.exists():
    DATA_FILE.write_text("{}")
joined = json.loads(DATA_FILE.read_text())

def save_joined():
    DATA_FILE.write_text(json.dumps(joined, indent=2))

# Check join
async def check_join(user_id, context):
    try:
        member = await context.bot.get_chat_member("@techirfantips", user_id)
        if member.status in ["member", "administrator", "creator"]:
            joined[str(user_id)] = True
            save_joined()
            return True
    except: pass
    return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) in joined or user_id == ADMIN_ID:
        await update.message.reply_text("Walaikum assalam bhai! Ab poocho jo poochna hai 😊")
        return

    keyboard = [
        [InlineKeyboardButton("Facebook Follow", url=FB_LINK)],
        [InlineKeyboardButton("Telegram Group Join", url=TG_GROUP)],
        [InlineKeyboardButton("YouTube Subscribe", url=YT_CHANNEL)],
        [InlineKeyboardButton("✅ Sab Kar Diya – Check Karo", callback_data="check")]
    ]
    await update.message.reply_text(
        "Bot use karne se pehle ye 3 kaam zaruri hain:\n\n"
        "1. Facebook follow\n2. @techirfantips group join\n3. YouTube @paksauditech subscribe\n\n"
        "Sab kar ke button daba do!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Button
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check":
        if await check_join(query.from_user.id, context) or query.from_user.id == ADMIN_ID:
            await query.edit_message_text("Mubarak! Ab bot full use karo 😊")
        else:
            await query.edit_message_text("Telegram group join karo pehle bhai!")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in joined and user_id != ADMIN_ID:
        await start(update, context)
        return

    # Rate limit
    now = time.time()
    if context.user_data.get("last", 0) > now - 2:
        await update.message.reply_text("Thodi der wait karo bhai 😅")
        return
    context.user_data["last"] = now

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json={"model": MODEL, "messages": [
                    {"role": "system", "content": "Reply only in Roman Urdu, short and natural."},
                    {"role": "user", "content": update.message.text}
                ]},
                headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": REFERER}
            ) as resp:
                data = await resp.json()
                reply = data["choices"][0]["message"]["content"] if "choices" in data else "Error bhai"
        except:
            reply = "Network issue hai, thodi der baad try karo"

    await update.message.reply_text(reply)

# Admin commands
async def grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = context.args[0]
        joined[uid] = True
        save_joined()
        await update.message.reply_text(f"Granted {uid}")
    except:
        await update.message.reply_text("Usage: /grant user_id")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(f"Total users: {len(joined)}")

# Run
app = Application.builder().token(TOKEN).concurrent_updates(True).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("grant", grant))
app.add_handler(CommandHandler("stats", stats))

print("Grok-4 Bot Started – 24/7 Ready!")
app.run_polling(drop_pending_updates=True)
