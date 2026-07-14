from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # miqdor (gramm yoki ml)
    unit: Mapped[str] = mapped_column(String(10), default="g")  # "g" yoki "l"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
