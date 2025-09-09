import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

TG_BOT_TOKEN = os.environ.get("8326139344:AAEOLrtzClSeNkRIpOglWGya32nOPe8hGAk")
CHANNEL_ID = int(os.environ.get("-1002322372180"))
DB_FILE = "movies.json"

def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def scrape_channel(bot):
    print("📥 Scraping channel messages...")
    db = load_db()
    last_id = 0
    while True:
        history = await bot.get_chat_history(
            chat_id=CHANNEL_ID,
            limit=100,
            offset_id=last_id,
            reverse=True
        )
        if not history:
            break
        for msg in history:
            text = msg.text or msg.caption
            if text:
                db[str(msg.message_id)] = text.strip().lower()
            last_id = msg.message_id
        if len(history) < 100:
            break
    save_db(db)
    print(f"✅ Scraping complete. Total movies saved: {len(db)}")

async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CHANNEL_ID:
        return
    text = update.message.text or update.message.caption
    if text:
        db = load_db()
        db[str(update.message.message_id)] = text.strip().lower()
        save_db(db)

async def search_and_forward(query, update, context):
    db = load_db()
    query = query.lower()
    for msg_id, text in db.items():
        if query in text and "480p" in text:
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=int(msg_id)
            )
            await update.message.reply_text("✅ 480p version mil gaya aur forward kar diya.")
            return
    await update.message.reply_text("❌ Movie ka 480p version channel me nahi mila.")

async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠ Example: /request Salaar")
        return
    query = " ".join(context.args)
    await search_and_forward(query, update, context)

async def normal_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        query = update.message.text.strip()
        if len(query) >= 3:
            await search_and_forward(query, update, context)

async def main():
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    async with app:
        await scrape_channel(app.bot)

    app.add_handler(MessageHandler(filters.Chat(CHANNEL_ID), save_movie))
    app.add_handler(CommandHandler("request", request))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, normal_text))

    print("🤖 Bot is running...")
    await app.run_polling()

if _name_ == "_main_":
    asyncio.run(main())