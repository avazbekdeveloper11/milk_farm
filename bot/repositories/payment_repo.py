from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.payment import Payment
from bot.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_customer_total_payments(self, customer_id: int) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.customer_id == customer_id
            )
        )
        return float(result.scalar())

    async def get_customer_payments(self, customer_id: int) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.customer_id == customer_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())
