from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.sale import Sale
from bot.repositories.sale_repo import SaleRepository
from bot.schemas.sale import SaleCreate


class SaleService:
    def __init__(self, session: AsyncSession):
        self.repo = SaleRepository(session)

    async def create(self, data: SaleCreate) -> Sale:
        total_amount = sum(
            item.quantity * item.unit_price for item in data.items
        )
        debt_amount = total_amount - data.paid_amount

        items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in data.items
        ]

        return await self.repo.create_with_items(
            customer_id=data.customer_id,
            total_amount=total_amount,
            paid_amount=data.paid_amount,
            debt_amount=debt_amount,
            items=items,
        )

    async def get_today_sales(self) -> list[Sale]:
        return await self.repo.get_today_sales()

    async def get_today_stats(self) -> dict:
        return await self.repo.get_today_stats()
