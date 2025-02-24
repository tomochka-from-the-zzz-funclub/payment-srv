import threading
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from yookassa import Configuration

from app.infrastructure.db.Settings import settings
from app.infrastructure.schedulers.scheduler import scheduler
from app.presentation.payment_router import payment
from app.services.telegram.telegram_service import TelegramService

load_dotenv()
telegram_service = TelegramService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_thread = threading.Thread(target=telegram_service.run_telegram_bot)
    bot_thread.start()
    scheduler.start()
    yield
    scheduler.shutdown()


Configuration.account_id = settings.ACCOUNT_ID
Configuration.secret_key = settings.SECRET_KEY

app = FastAPI(lifespan=lifespan)

app.include_router(payment, prefix='/payment', tags=['payment'])
