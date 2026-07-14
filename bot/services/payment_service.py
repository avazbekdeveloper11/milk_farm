from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.payment import Payment
from bot.repositories.payment_repo import PaymentRepository
from bot.schemas.sale import PaymentCreate


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.repo = PaymentRepository(session)

    async def create(self, data: PaymentCreate) -> Payment:
        return await self.repo.create(
            customer_id=data.customer_id,
            amount=data.amount,
            note=data.note,
        )

    async def get_customer_payments(self, customer_id: int) -> list[Payment]:
        return await self.repo.get_customer_payments(customer_id)
