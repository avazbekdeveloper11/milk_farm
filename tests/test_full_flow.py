"""
To'liq biznes jarayonini sinab ko'rish:
1. Mahsulot qo'shish
2. Mijoz qo'shish
3. Savdo qilish (qisman to'lov)
4. Qarz hosil bo'lishi
5. Qarz to'lash
6. Hisobot tekshirish
"""

import pytest

from bot.schemas.customer import CustomerCreate
from bot.schemas.product import ProductCreate
from bot.schemas.sale import PaymentCreate, SaleCreate, SaleItemCreate
from bot.services.customer_service import CustomerService
from bot.services.payment_service import PaymentService
from bot.services.product_service import ProductService
from bot.services.sale_service import SaleService


@pytest.mark.asyncio
async def test_full_business_flow(session):
    """To'liq biznes jarayoni"""

    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)
    payment_service = PaymentService(session)

    # ========== 1. MAHSULOTLAR QO'SHISH ==========
    print("\n=== 1. MAHSULOTLAR QO'SHISH ===")

    kefir = await product_service.create(
        ProductCreate(name="Kefir 1%", price=15000, weight_gram=500)
    )
    assert kefir.id is not None
    assert kefir.name == "Kefir 1%"
    print(f"✅ Kefir qo'shildi: {kefir.name} - {int(kefir.price):,} so'm")

    smetana = await product_service.create(
        ProductCreate(name="Smetana 20%", price=25000, weight_gram=400)
    )
    assert smetana.id is not None
    print(f"✅ Smetana qo'shildi: {smetana.name} - {int(smetana.price):,} so'm")

    tvorog = await product_service.create(
        ProductCreate(name="Tvorog", price=35000, weight_gram=500)
    )
    assert tvorog.id is not None
    print(f"✅ Tvorog qo'shildi: {tvorog.name} - {int(tvorog.price):,} so'm")

    # Mahsulotlar ro'yxati
    products = await product_service.get_active()
    assert len(products) == 3
    print(f"📦 Jami mahsulotlar: {len(products)} ta")

    # ========== 2. MIJOZLAR QO'SHISH ==========
    print("\n=== 2. MIJOZLAR QO'SHISH ===")

    ali = await customer_service.create(
        CustomerCreate(name="Ali Valiyev", phone="+998901234567")
    )
    assert ali.id is not None
    assert ali.phone == "+998901234567"
    print(f"✅ Mijoz qo'shildi: {ali.name} ({ali.phone})")

    vali = await customer_service.create(
        CustomerCreate(name="Vali Aliyev", phone="+998907654321")
    )
    assert vali.id is not None
    print(f"✅ Mijoz qo'shildi: {vali.name} ({vali.phone})")

    soli = await customer_service.create(
        CustomerCreate(name="Soli Karimov")  # telefonsiz
    )
    assert soli.id is not None
    assert soli.phone is None
    print(f"✅ Mijoz qo'shildi: {soli.name} (telefonsiz)")

    # Mijozlar ro'yxati
    customers = await customer_service.get_all()
    assert len(customers) == 3
    print(f"👥 Jami mijozlar: {len(customers)} ta")

    # Qidirish
    found = await customer_service.search("ali")
    assert len(found) == 2  # Ali va Vali Aliyev
    print(f"🔍 'ali' bo'yicha topildi: {len(found)} ta")

    # ========== 3. SAVDO QILISH (TO'LIQ TO'LOV) ==========
    print("\n=== 3. SAVDO #1 - TO'LIQ TO'LOV ===")

    sale1 = await sale_service.create(
        SaleCreate(
            customer_id=ali.id,
            items=[
                SaleItemCreate(product_id=kefir.id, quantity=2, unit_price=15000),
            ],
            paid_amount=30000,  # to'liq to'lov
        )
    )
    assert sale1.id is not None
    assert float(sale1.total_amount) == 30000
    assert float(sale1.paid_amount) == 30000
    assert float(sale1.debt_amount) == 0
    print(f"✅ Savdo #{sale1.id}: {int(sale1.total_amount):,} so'm (to'liq to'landi)")

    ali_debt = await customer_service.get_debt(ali.id)
    assert ali_debt == 0
    print(f"💳 {ali.name} qarzi: {int(ali_debt):,} so'm")

    # ========== 4. SAVDO QILISH (QISMAN TO'LOV - QARZ HOSIL BO'LADI) ==========
    print("\n=== 4. SAVDO #2 - QISMAN TO'LOV (QARZ) ===")

    sale2 = await sale_service.create(
        SaleCreate(
            customer_id=vali.id,
            items=[
                SaleItemCreate(product_id=kefir.id, quantity=3, unit_price=15000),   # 45,000
                SaleItemCreate(product_id=smetana.id, quantity=2, unit_price=25000), # 50,000
            ],
            paid_amount=50000,  # 95,000 dan 50,000 to'ladi
        )
    )
    assert sale2.id is not None
    assert float(sale2.total_amount) == 95000
    assert float(sale2.paid_amount) == 50000
    assert float(sale2.debt_amount) == 45000
    print(f"✅ Savdo #{sale2.id}: {int(sale2.total_amount):,} so'm")
    print(f"   💵 Naqd: {int(sale2.paid_amount):,} so'm")
    print(f"   💳 Qarz: {int(sale2.debt_amount):,} so'm")

    vali_debt = await customer_service.get_debt(vali.id)
    assert vali_debt == 45000
    print(f"💳 {vali.name} qarzi: {int(vali_debt):,} so'm")

    # ========== 5. YANA SAVDO (TO'LIQ QARZGA) ==========
    print("\n=== 5. SAVDO #3 - TO'LIQ QARZGA ===")

    sale3 = await sale_service.create(
        SaleCreate(
            customer_id=soli.id,
            items=[
                SaleItemCreate(product_id=tvorog.id, quantity=2, unit_price=35000),  # 70,000
            ],
            paid_amount=0,  # hech narsa to'lamadi
        )
    )
    assert float(sale3.total_amount) == 70000
    assert float(sale3.paid_amount) == 0
    assert float(sale3.debt_amount) == 70000
    print(f"✅ Savdo #{sale3.id}: {int(sale3.total_amount):,} so'm (to'liq qarzga)")

    soli_debt = await customer_service.get_debt(soli.id)
    assert soli_debt == 70000
    print(f"💳 {soli.name} qarzi: {int(soli_debt):,} so'm")

    # ========== 6. BUGUNGI SAVDO HISOBOTI ==========
    print("\n=== 6. BUGUNGI SAVDO HISOBOTI ===")

    stats = await sale_service.get_today_stats()
    assert stats["count"] == 3
    assert stats["total"] == 195000  # 30k + 95k + 70k
    assert stats["paid"] == 80000    # 30k + 50k + 0
    assert stats["debt"] == 115000   # 0 + 45k + 70k
    print(f"📈 Savdolar soni: {stats['count']}")
    print(f"💰 Jami: {int(stats['total']):,} so'm")
    print(f"💵 Naqd: {int(stats['paid']):,} so'm")
    print(f"💳 Qarz: {int(stats['debt']):,} so'm")

    # ========== 7. QARZ TO'LASH ==========
    print("\n=== 7. QARZ TO'LASH ===")

    # Vali qisman to'laydi
    payment1 = await payment_service.create(
        PaymentCreate(customer_id=vali.id, amount=20000, note="Qisman to'lov")
    )
    assert payment1.id is not None
    print(f"✅ To'lov #{payment1.id}: {vali.name} - {int(payment1.amount):,} so'm")

    vali_debt_after = await customer_service.get_debt(vali.id)
    assert vali_debt_after == 25000  # 45000 - 20000
    print(f"💳 {vali.name} qolgan qarzi: {int(vali_debt_after):,} so'm")

    # Vali to'liq to'laydi
    payment2 = await payment_service.create(
        PaymentCreate(customer_id=vali.id, amount=25000, note="Qolgan qarz")
    )
    vali_final_debt = await customer_service.get_debt(vali.id)
    assert vali_final_debt == 0
    print(f"✅ To'lov #{payment2.id}: {vali.name} - {int(payment2.amount):,} so'm")
    print(f"💳 {vali.name} qarzi yo'q!")

    # Soli qisman to'laydi
    payment3 = await payment_service.create(
        PaymentCreate(customer_id=soli.id, amount=30000)
    )
    soli_debt_after = await customer_service.get_debt(soli.id)
    assert soli_debt_after == 40000  # 70000 - 30000
    print(f"✅ To'lov #{payment3.id}: {soli.name} - {int(payment3.amount):,} so'm")
    print(f"💳 {soli.name} qolgan qarzi: {int(soli_debt_after):,} so'm")

    # ========== 8. YAKUNIY QARZLAR HISOBOTI ==========
    print("\n=== 8. YAKUNIY QARZLAR HISOBOTI ===")

    all_customers = await customer_service.get_all()
    total_debt = 0
    debtors = []

    for customer in all_customers:
        debt = await customer_service.get_debt(customer.id)
        if debt > 0:
            debtors.append((customer.name, debt))
            total_debt += debt
        print(f"👤 {customer.name}: {int(debt):,} so'm qarz")

    assert len(debtors) == 1  # faqat Soli
    assert total_debt == 40000
    print(f"\n📊 Jami qarzdorlar: {len(debtors)} ta")
    print(f"📊 Jami qarz: {int(total_debt):,} so'm")

    # ========== 9. MAHSULOT YANGILASH VA O'CHIRISH ==========
    print("\n=== 9. MAHSULOT OPERATSIYALARI ===")

    from bot.schemas.product import ProductUpdate

    # Narx yangilash
    updated_kefir = await product_service.update(
        kefir.id, ProductUpdate(price=16000)
    )
    assert float(updated_kefir.price) == 16000
    print(f"✅ {kefir.name} narxi yangilandi: {int(updated_kefir.price):,} so'm")

    # O'chirish (is_active=False)
    await product_service.update(tvorog.id, ProductUpdate(is_active=False))
    active_products = await product_service.get_active()
    assert len(active_products) == 2
    print(f"✅ {tvorog.name} o'chirildi. Faol mahsulotlar: {len(active_products)} ta")

    print("\n" + "=" * 50)
    print("✅ BARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")
    print("=" * 50)


@pytest.mark.asyncio
async def test_edge_cases(session):
    """Chegaraviy holatlar"""

    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)
    payment_service = PaymentService(session)

    print("\n=== CHEGARAVIY HOLATLAR ===")

    # 1. Bo'sh bazada qidirish
    customers = await customer_service.get_all()
    assert len(customers) == 0
    print("✅ Bo'sh bazada mijozlar: 0 ta")

    # 2. Mavjud bo'lmagan ID
    not_found = await customer_service.get_by_id(9999)
    assert not_found is None
    print("✅ Mavjud bo'lmagan mijoz: None")

    # 3. Qarz yo'q bo'lganda
    customer = await customer_service.create(CustomerCreate(name="Test"))
    debt = await customer_service.get_debt(customer.id)
    assert debt == 0
    print("✅ Yangi mijoz qarzi: 0")

    # 4. Bugungi savdo - bo'sh
    stats = await sale_service.get_today_stats()
    assert stats["count"] == 0
    assert stats["total"] == 0
    print("✅ Bo'sh bugungi hisobot: count=0, total=0")

    # 5. Minimal qiymatlar
    product = await product_service.create(
        ProductCreate(name="A", price=1, weight_gram=1)
    )
    assert product.id is not None
    print("✅ Minimal mahsulot qo'shildi")

    # 6. Katta qiymatlar
    big_product = await product_service.create(
        ProductCreate(name="Katta mahsulot", price=99999999, weight_gram=99999)
    )
    assert big_product.id is not None
    print(f"✅ Katta narxli mahsulot: {int(big_product.price):,} so'm")

    # 7. Ko'p savdolar bir mijozga
    for i in range(5):
        await sale_service.create(
            SaleCreate(
                customer_id=customer.id,
                items=[SaleItemCreate(product_id=product.id, quantity=1, unit_price=1)],
                paid_amount=0,
            )
        )

    debt = await customer_service.get_debt(customer.id)
    assert debt == 5  # 5 x 1 so'm
    print(f"✅ 5 ta savdodan keyin qarz: {int(debt)} so'm")

    # 8. Ko'p to'lovlar
    for i in range(5):
        await payment_service.create(
            PaymentCreate(customer_id=customer.id, amount=1)
        )

    final_debt = await customer_service.get_debt(customer.id)
    assert final_debt == 0  # 5 - 5 = 0
    print("✅ 5 ta to'lovdan keyin qarz: 0")

    print("\n✅ CHEGARAVIY HOLATLAR TESTLARI O'TDI!")


@pytest.mark.asyncio
async def test_concurrent_operations(session):
    """Bir vaqtda bir nechta operatsiya"""

    product_service = ProductService(session)
    customer_service = CustomerService(session)
    sale_service = SaleService(session)

    print("\n=== KO'P OPERATSIYALAR ===")

    # 10 ta mahsulot
    products = []
    for i in range(10):
        p = await product_service.create(
            ProductCreate(name=f"Mahsulot {i+1}", price=10000 * (i+1), weight_gram=500)
        )
        products.append(p)
    print(f"✅ {len(products)} ta mahsulot qo'shildi")

    # 20 ta mijoz
    customers = []
    for i in range(20):
        c = await customer_service.create(
            CustomerCreate(name=f"Mijoz {i+1}", phone=f"+99890000000{i:02d}")
        )
        customers.append(c)
    print(f"✅ {len(customers)} ta mijoz qo'shildi")

    # Har bir mijozga savdo
    for i, customer in enumerate(customers):
        product = products[i % len(products)]
        await sale_service.create(
            SaleCreate(
                customer_id=customer.id,
                items=[
                    SaleItemCreate(
                        product_id=product.id,
                        quantity=i + 1,
                        unit_price=float(product.price),
                    )
                ],
                paid_amount=0,
            )
        )
    print(f"✅ {len(customers)} ta savdo yaratildi")

    # Hisobot
    stats = await sale_service.get_today_stats()
    assert stats["count"] == 20
    print(f"📊 Bugungi savdolar: {stats['count']} ta")
    print(f"📊 Jami summa: {int(stats['total']):,} so'm")
    print(f"📊 Jami qarz: {int(stats['debt']):,} so'm")

    print("\n✅ KO'P OPERATSIYALAR TESTLARI O'TDI!")
