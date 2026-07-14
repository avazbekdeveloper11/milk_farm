from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.database.session import async_session
from bot.models.user import AuthorizedUser


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
        else:
            user_id = event.from_user.id

        async with async_session() as session:
            result = await session.execute(
                select(AuthorizedUser).where(AuthorizedUser.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()

        data["is_authorized"] = user is not None

        return await handler(event, data)
