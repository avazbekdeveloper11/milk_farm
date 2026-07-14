from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.product import Product
from bot.repositories.product_repo import ProductRepository
from bot.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: AsyncSession):
        self.repo = ProductRepository(session)

    async def create(self, data: ProductCreate) -> Product:
        return await self.repo.create(
            name=data.name,
            price=data.price,
            amount=data.amount,
            unit=data.unit,
        )

    async def get_all(self) -> list[Product]:
        return await self.repo.get_all()

    async def get_active(self) -> list[Product]:
        return await self.repo.get_active()

    async def get_by_id(self, id: int) -> Product | None:
        return await self.repo.get_by_id(id)

    async def update(self, id: int, data: ProductUpdate) -> Product | None:
        return await self.repo.update(
            id,
            name=data.name,
            price=data.price,
            amount=data.amount,
            unit=data.unit,
            is_active=data.is_active,
        )

    async def delete(self, id: int) -> bool:
        return await self.repo.delete(id)
