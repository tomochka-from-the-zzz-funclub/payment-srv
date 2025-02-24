import asyncio
from fastapi import HTTPException
from dotenv import load_dotenv
import os

from telegram import Update
from telegram.ext import CommandHandler, Application


class TelegramService:
    async def send_message(self, chat_id, text):
        try:
            bot = application.bot
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            raise HTTPException(status_code=500)

    async def start(self, update: Update, context):
        chat_id = update.message.chat.id
        await update.message.reply_text(f"Привет! {chat_id}")

    def run_telegram_bot(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        application.add_handler(CommandHandler("start", self.start))
        loop.run_until_complete(application.run_polling(drop_pending_updates=True, stop_signals=None))


load_dotenv()
TOKEN = os.getenv('TG_TOKEN')
application = Application.builder().token(TOKEN).build()
