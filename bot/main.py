import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramServerError

from bot.config import settings
from bot.database.session import engine
from bot.handlers import setup_routers
from bot.middlewares import AuthMiddleware
from bot.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_DELAY = 5


async def on_startup():
    os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    router = setup_routers()
    router.message.middleware(AuthMiddleware())
    router.callback_query.middleware(AuthMiddleware())
    dp.include_router(router)

    await on_startup()

    logger.info("Bot started")

    for attempt in range(MAX_RETRIES):
        try:
            await dp.start_polling(bot)
            break
        except TelegramServerError as e:
            logger.warning(f"Telegram server error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Exiting.")
                raise


if __name__ == "__main__":
    asyncio.run(main())
