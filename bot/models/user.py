from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base, TimestampMixin


class AuthorizedUser(Base, TimestampMixin):
    __tablename__ = "authorized_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
