from pydantic import BaseModel


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class SaleCreate(BaseModel):
    customer_id: int
    items: list[SaleItemCreate]
    paid_amount: float


class PaymentCreate(BaseModel):
    customer_id: int
    amount: float
    note: str | None = None
