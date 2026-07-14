import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramServerError

from bot.config import settings
from bot.database.session import engine
from bot.handlers import setup_routers
from bot.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 10
RETRY_DELAY = 5


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(setup_routers())

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
