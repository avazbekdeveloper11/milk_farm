from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: float
    amount: int  # miqdor (gramm yoki ml)
    unit: str = "g"  # "g" yoki "l"


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    amount: int | None = None
    unit: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    amount: int
    unit: str
    is_active: bool
