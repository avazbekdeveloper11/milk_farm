from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.sale import Sale, SaleItem
from bot.repositories.base import BaseRepository


class SaleRepository(BaseRepository[Sale]):
    def __init__(self, session: AsyncSession):
        super().__init__(Sale, session)

    async def create_with_items(
        self,
        customer_id: int,
        total_amount: float,
        paid_amount: float,
        debt_amount: float,
        items: list[dict],
    ) -> Sale:
        sale = Sale(
            customer_id=customer_id,
            total_amount=total_amount,
            paid_amount=paid_amount,
            debt_amount=debt_amount,
        )
        self.session.add(sale)
        await self.session.flush()

        for item in items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["quantity"] * item["unit_price"],
            )
            self.session.add(sale_item)

        await self.session.commit()
        await self.session.refresh(sale)
        return sale

    async def get_today_sales(self) -> list[Sale]:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        result = await self.session.execute(
            select(Sale)
            .options(selectinload(Sale.customer), selectinload(Sale.items))
            .where(Sale.created_at >= today, Sale.created_at < tomorrow)
        )
        return list(result.scalars().all())

    async def get_today_stats(self) -> dict:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        result = await self.session.execute(
            select(
                func.count(Sale.id).label("count"),
                func.coalesce(func.sum(Sale.total_amount), 0).label("total"),
                func.coalesce(func.sum(Sale.paid_amount), 0).label("paid"),
                func.coalesce(func.sum(Sale.debt_amount), 0).label("debt"),
            ).where(Sale.created_at >= today, Sale.created_at < tomorrow)
        )
        row = result.one()
        return {
            "count": row.count,
            "total": float(row.total),
            "paid": float(row.paid),
            "debt": float(row.debt),
        }

    async def get_customer_total_debt(self, customer_id: int) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Sale.debt_amount), 0)).where(
                Sale.customer_id == customer_id
            )
        )
        return float(result.scalar())

    async def get_monthly_stats(self) -> dict:
        today = date.today()
        first_day = today.replace(day=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        result = await self.session.execute(
            select(
                func.count(Sale.id).label("count"),
                func.coalesce(func.sum(Sale.total_amount), 0).label("total"),
                func.coalesce(func.sum(Sale.paid_amount), 0).label("paid"),
                func.coalesce(func.sum(Sale.debt_amount), 0).label("debt"),
            ).where(Sale.created_at >= first_day, Sale.created_at < next_month)
        )
        row = result.one()
        return {
            "count": row.count,
            "total": float(row.total),
            "paid": float(row.paid),
            "debt": float(row.debt),
        }

    async def get_yearly_stats(self) -> dict:
        today = date.today()
        first_day = today.replace(month=1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)
        result = await self.session.execute(
            select(
                func.count(Sale.id).label("count"),
                func.coalesce(func.sum(Sale.total_amount), 0).label("total"),
                func.coalesce(func.sum(Sale.paid_amount), 0).label("paid"),
                func.coalesce(func.sum(Sale.debt_amount), 0).label("debt"),
            ).where(Sale.created_at >= first_day, Sale.created_at < next_year)
        )
        row = result.one()
        return {
            "count": row.count,
            "total": float(row.total),
            "paid": float(row.paid),
            "debt": float(row.debt),
        }
