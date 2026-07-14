from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.product import Product
from bot.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_active(self) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.is_active == True)
        )
        return list(result.scalars().all())
