import pytest

from bot.schemas.product import ProductCreate, ProductUpdate
from bot.services.product_service import ProductService


@pytest.mark.asyncio
async def test_create_product(session):
    service = ProductService(session)

    product = await service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )

    assert product.id is not None
    assert product.name == "Kefir"
    assert float(product.price) == 15000
    assert product.weight_gram == 500
    assert product.is_active is True


@pytest.mark.asyncio
async def test_get_product_by_id(session):
    service = ProductService(session)

    created = await service.create(
        ProductCreate(name="Smetana", price=20000, weight_gram=400)
    )

    product = await service.get_by_id(created.id)

    assert product is not None
    assert product.name == "Smetana"


@pytest.mark.asyncio
async def test_get_all_products(session):
    service = ProductService(session)

    await service.create(ProductCreate(name="Kefir", price=15000, weight_gram=500))
    await service.create(ProductCreate(name="Smetana", price=20000, weight_gram=400))

    products = await service.get_all()

    assert len(products) == 2


@pytest.mark.asyncio
async def test_get_active_products(session):
    service = ProductService(session)

    p1 = await service.create(ProductCreate(name="Kefir", price=15000, weight_gram=500))
    await service.create(ProductCreate(name="Smetana", price=20000, weight_gram=400))

    await service.update(p1.id, ProductUpdate(is_active=False))

    active = await service.get_active()

    assert len(active) == 1
    assert active[0].name == "Smetana"


@pytest.mark.asyncio
async def test_update_product(session):
    service = ProductService(session)

    product = await service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )

    updated = await service.update(
        product.id, ProductUpdate(name="Kefir 1%", price=16000)
    )

    assert updated.name == "Kefir 1%"
    assert float(updated.price) == 16000
    assert updated.weight_gram == 500


@pytest.mark.asyncio
async def test_delete_product(session):
    service = ProductService(session)

    product = await service.create(
        ProductCreate(name="Kefir", price=15000, weight_gram=500)
    )

    result = await service.delete(product.id)

    assert result is True
    assert await service.get_by_id(product.id) is None
