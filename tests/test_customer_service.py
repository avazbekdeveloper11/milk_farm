import pytest

from bot.schemas.customer import CustomerCreate, CustomerUpdate
from bot.services.customer_service import CustomerService


@pytest.mark.asyncio
async def test_create_customer(session):
    service = CustomerService(session)

    customer = await service.create(
        CustomerCreate(name="Ali Valiyev", phone="+998901234567")
    )

    assert customer.id is not None
    assert customer.name == "Ali Valiyev"
    assert customer.phone == "+998901234567"


@pytest.mark.asyncio
async def test_create_customer_without_phone(session):
    service = CustomerService(session)

    customer = await service.create(CustomerCreate(name="Vali Aliyev"))

    assert customer.id is not None
    assert customer.name == "Vali Aliyev"
    assert customer.phone is None


@pytest.mark.asyncio
async def test_get_customer_by_id(session):
    service = CustomerService(session)

    created = await service.create(
        CustomerCreate(name="Ali Valiyev", phone="+998901234567")
    )

    customer = await service.get_by_id(created.id)

    assert customer is not None
    assert customer.name == "Ali Valiyev"


@pytest.mark.asyncio
async def test_get_all_customers(session):
    service = CustomerService(session)

    await service.create(CustomerCreate(name="Ali"))
    await service.create(CustomerCreate(name="Vali"))
    await service.create(CustomerCreate(name="Soli"))

    customers = await service.get_all()

    assert len(customers) == 3


@pytest.mark.asyncio
async def test_search_customers(session):
    service = CustomerService(session)

    await service.create(CustomerCreate(name="Ali Valiyev"))
    await service.create(CustomerCreate(name="Vali Aliyev"))
    await service.create(CustomerCreate(name="Soli Karimov"))

    results = await service.search("ali")

    assert len(results) == 2


@pytest.mark.asyncio
async def test_update_customer(session):
    service = CustomerService(session)

    customer = await service.create(
        CustomerCreate(name="Ali Valiyev", phone="+998901234567")
    )

    updated = await service.update(
        customer.id, CustomerUpdate(name="Ali Valiyevich")
    )

    assert updated.name == "Ali Valiyevich"
    assert updated.phone == "+998901234567"


@pytest.mark.asyncio
async def test_delete_customer(session):
    service = CustomerService(session)

    customer = await service.create(CustomerCreate(name="Ali"))

    result = await service.delete(customer.id)

    assert result is True
    assert await service.get_by_id(customer.id) is None


@pytest.mark.asyncio
async def test_get_debt_no_sales(session):
    service = CustomerService(session)

    customer = await service.create(CustomerCreate(name="Ali"))

    debt = await service.get_debt(customer.id)

    assert debt == 0
