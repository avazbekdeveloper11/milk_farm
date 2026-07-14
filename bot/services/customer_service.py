from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.customer import Customer
from bot.repositories.customer_repo import CustomerRepository
from bot.repositories.payment_repo import PaymentRepository
from bot.repositories.sale_repo import SaleRepository
from bot.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, session: AsyncSession):
        self.repo = CustomerRepository(session)
        self.sale_repo = SaleRepository(session)
        self.payment_repo = PaymentRepository(session)

    async def create(self, data: CustomerCreate) -> Customer:
        return await self.repo.create(name=data.name, phone=data.phone)

    async def get_all(self) -> list[Customer]:
        return await self.repo.get_all()

    async def get_by_id(self, id: int) -> Customer | None:
        return await self.repo.get_by_id(id)

    async def search(self, query: str) -> list[Customer]:
        return await self.repo.search(query)

    async def update(self, id: int, data: CustomerUpdate) -> Customer | None:
        return await self.repo.update(id, name=data.name, phone=data.phone)

    async def delete(self, id: int) -> bool:
        return await self.repo.delete(id)

    async def get_debt(self, customer_id: int) -> float:
        total_debt = await self.sale_repo.get_customer_total_debt(customer_id)
        total_paid = await self.payment_repo.get_customer_total_payments(customer_id)
        return total_debt - total_paid
