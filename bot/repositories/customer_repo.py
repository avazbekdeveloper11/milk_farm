from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.customer import Customer
from bot.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession):
        super().__init__(Customer, session)

    async def search(self, query: str) -> list[Customer]:
        """Ism yoki telefon bo'yicha qidirish"""
        from sqlalchemy import or_
        result = await self.session.execute(
            select(Customer).where(
                or_(
                    Customer.name.ilike(f"%{query}%"),
                    Customer.phone.ilike(f"%{query}%")
                )
            )
        )
        return list(result.scalars().all())

    async def get_by_phone(self, phone: str) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.phone == phone)
        )
        return result.scalar_one_or_none()
