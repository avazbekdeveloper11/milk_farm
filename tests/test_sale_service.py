import pytest

from bot.schemas.customer import CustomerCreate
from bot.schemas.product import ProductCreate
from bot.schemas.sale import PaymentCreate, SaleCreate, SaleItemCreate
from bot.services.customer_service import CustomerService
from bot.services.payment_service import PaymentService
from bot.services.product_service import ProductService
from bot.services.sale_service import SaleService


@pytest.mark.asyncio
async def test_create_sale_full_payment(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    sale = await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=2, unit_price=15000)],
            paid_amount=30000,
        )
    )

    assert sale.id is not None
    assert float(sale.total_amount) == 30000
    assert float(sale.paid_amount) == 30000
    assert float(sale.debt_amount) == 0


@pytest.mark.asyncio
async def test_create_sale_partial_payment(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    product = await product_service.create(
        ProductCreate(name="Smetana", price=20000, weight_gram=400)
    )
    customer = await customer_service.create(CustomerCreate(name="Vali"))

    sale = await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=3, unit_price=20000)],
            paid_amount=40000,
        )
    )

    assert float(sale.total_amount) == 60000
    assert float(sale.paid_amount) == 40000
    assert float(sale.debt_amount) == 20000


@pytest.mark.asyncio
async def test_create_sale_no_payment(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Soli"))

    sale = await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=2, unit_price=15000)],
            paid_amount=0,
        )
    )

    assert float(sale.total_amount) == 30000
    assert float(sale.paid_amount) == 0
    assert float(sale.debt_amount) == 30000


@pytest.mark.asyncio
async def test_create_sale_multiple_products(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    kefir = await product_service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )
    smetana = await product_service.create(
        ProductCreate(name="Smetana", price=20000, weight_gram=400)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    sale = await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[
                SaleItemCreate(product_id=kefir.id, quantity=2, unit_price=15000),
                SaleItemCreate(product_id=smetana.id, quantity=1, unit_price=20000),
            ],
            paid_amount=30000,
        )
    )

    assert float(sale.total_amount) == 50000
    assert float(sale.paid_amount) == 30000
    assert float(sale.debt_amount) == 20000


@pytest.mark.asyncio
async def test_customer_debt_calculation(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=10000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=2, unit_price=10000)],
            paid_amount=10000,
        )
    )

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=3, unit_price=10000)],
            paid_amount=20000,
        )
    )

    debt = await customer_service.get_debt(customer.id)

    assert debt == 20000


@pytest.mark.asyncio
async def test_customer_debt_after_payment(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)
    payment_service = PaymentService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=10000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=5, unit_price=10000)],
            paid_amount=20000,
        )
    )

    debt_before = await customer_service.get_debt(customer.id)
    assert debt_before == 30000

    await payment_service.create(
        PaymentCreate(customer_id=customer.id, amount=15000, note="Qisman to'lov")
    )

    debt_after = await customer_service.get_debt(customer.id)
    assert debt_after == 15000


@pytest.mark.asyncio
async def test_customer_debt_full_payment(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)
    payment_service = PaymentService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=10000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=3, unit_price=10000)],
            paid_amount=0,
        )
    )

    await payment_service.create(
        PaymentCreate(customer_id=customer.id, amount=30000, note="To'liq to'lov")
    )

    debt = await customer_service.get_debt(customer.id)
    assert debt == 0


@pytest.mark.asyncio
async def test_get_today_stats(session):
    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    product = await product_service.create(
        ProductCreate(name="Kefir", price=10000, weight_gram=500)
    )
    customer = await customer_service.create(CustomerCreate(name="Ali"))

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=2, unit_price=10000)],
            paid_amount=15000,
        )
    )

    await sale_service.create(
        SaleCreate(
            customer_id=customer.id,
            items=[SaleItemCreate(product_id=product.id, quantity=3, unit_price=10000)],
            paid_amount=20000,
        )
    )

    stats = await sale_service.get_today_stats()

    assert stats["count"] == 2
    assert stats["total"] == 50000
    assert stats["paid"] == 35000
    assert stats["debt"] == 15000
