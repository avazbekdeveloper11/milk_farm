from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.session import async_session
from bot.keyboards.menus import (
    cancel_keyboard,
    confirm_keyboard,
    customer_select_keyboard,
    main_menu,
)
from bot.schemas.sale import PaymentCreate, SaleCreate, SaleItemCreate
from bot.services.customer_service import CustomerService
from bot.services.payment_service import PaymentService
from bot.services.product_service import ProductService
from bot.services.sale_service import SaleService
from bot.states.forms import PaymentForm, SaleForm

router = Router()


def parse_number(text: str, is_float: bool = False) -> float | int | None:
    try:
        cleaned = text.replace(",", "").replace(" ", "").strip()
        return float(cleaned) if is_float else int(cleaned)
    except ValueError:
        return None


def generate_receipt(
    customer_name: str,
    customer_phone: str | None,
    products_data: list[dict],
    total: float,
    paid: float,
    debt: float,
    old_debt: float,
    sale_id: int,
) -> str:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    phone_str = customer_phone or "kiritilmagan"

    lines = [
        "━━━━━━━━━━ <b>CHEK</b> ━━━━━━━━━━",
        f"📋 Savdo #{sale_id}",
        f"👤 Mijoz: {customer_name}",
        f"📞 Telefon: {phone_str}",
        f"📅 Sana: {now}",
        "",
        "<b>Mahsulotlar:</b>",
    ]

    for i, item in enumerate(products_data, 1):
        name = item["name"]
        amount_str = format_amount(item["amount"], item["unit"])
        qty = item["quantity"]
        price = item["price"]
        subtotal = price * qty
        lines.append(
            f"{i}. {name} {amount_str}   x{qty} dona   x {int(price):,} = <b>{int(subtotal):,} so'm</b>"
        )

    lines.append("")
    lines.append(f"💰 <b>Jami: {int(total):,} so'm</b>")
    lines.append(f"💵 To'landi (naqd): {int(paid):,} so'm")
    lines.append(f"💳 Qarzga qoldi: {int(debt):,} so'm")
    lines.append("")

    total_debt = old_debt + debt
    if total_debt > 0:
        lines.append(f"📊 <b>Mijozning JAMI QARZI: {int(total_debt):,} so'm</b>")
    else:
        lines.append("✅ Mijozning qarzi yo'q")

    return "\n".join(lines)


def sale_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Yangi mijoz qo'shish", callback_data="sale_add_customer")],
        [InlineKeyboardButton(text="🔍 Mijoz qidirish", callback_data="sale_search_customer")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def overpay_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💳 Qarzdan ayirish", callback_data="overpay_subtract")],
        [InlineKeyboardButton(text="🔄 Qayta kiritish", callback_data="overpay_retry")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_amount(amount: int, unit: str) -> str:
    """Miqdorni formatlash"""
    if unit == "l":
        if amount >= 1000:
            return f"{amount / 1000:.1f} l"
        return f"{amount} ml"
    else:
        if amount >= 1000:
            return f"{amount / 1000:.1f} kg"
        return f"{amount} g"


def products_keyboard(available_products: dict, selected: dict) -> InlineKeyboardMarkup:
    """Mahsulotlar uchun inline tugmalar"""
    buttons = []
    for pid, p in available_products.items():
        qty = selected.get(pid, 0)
        if qty > 0:
            text = f"✅ {p['name']} x{qty}"
        else:
            text = f"📦 {p['name']} - {int(p['price']):,}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"sp_{pid}")])

    if selected:
        total = sum(available_products[pid]["price"] * qty for pid, qty in selected.items())
        buttons.append([InlineKeyboardButton(text=f"💰 Tayyor ({int(total):,} so'm)", callback_data="sp_done")])
        buttons.append([InlineKeyboardButton(text="🗑 Tozalash", callback_data="sp_clear")])

    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Son tanlash uchun tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="1", callback_data=f"qty_{product_id}_1"),
            InlineKeyboardButton(text="2", callback_data=f"qty_{product_id}_2"),
            InlineKeyboardButton(text="3", callback_data=f"qty_{product_id}_3"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data=f"qty_{product_id}_4"),
            InlineKeyboardButton(text="5", callback_data=f"qty_{product_id}_5"),
            InlineKeyboardButton(text="10", callback_data=f"qty_{product_id}_10"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="qty_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "🛒 Savdo")
async def start_sale(message: Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        customer_service = CustomerService(session)
        customers = await customer_service.get_all()

    if not customers:
        await message.answer(
            "🛒 <b>Yangi savdo</b>\n\n"
            "Mijozlar ro'yxati bo'sh.\n"
            "Avval mijoz qo'shing:",
            reply_markup=sale_menu_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(SaleForm.select_customer)
        return

    await state.set_state(SaleForm.select_customer)

    customer_buttons = []
    for c in customers:
        async with async_session() as session:
            cs = CustomerService(session)
            debt = await cs.get_debt(c.id)

        debt_str = f" 🔴 {int(debt):,}" if debt > 0 else ""
        text = f"{c.name}{debt_str}"
        customer_buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"sale_customer_{c.id}")]
        )

    customer_buttons.append([InlineKeyboardButton(text="➕ Yangi mijoz", callback_data="sale_add_customer")])
    customer_buttons.append([InlineKeyboardButton(text="🔍 Qidirish", callback_data="sale_search_customer")])
    customer_buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])

    await message.answer(
        "🛒 <b>Yangi savdo</b>\n\n"
        "Mijozni tanlang yoki yangi qo'shing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=customer_buttons),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.select_customer, F.data == "sale_add_customer")
async def sale_add_new_customer(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SaleForm.add_customer_name)
    await callback.message.edit_text(
        "👤 <b>Yangi mijoz qo'shish</b>\n\n"
        "Mijoz ismini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(SaleForm.add_customer_name)
async def process_new_customer_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa. Kamida 2 ta belgi:")
        return

    await state.update_data(new_customer_name=name)
    await state.set_state(SaleForm.add_customer_phone)
    await message.answer(
        "📞 Telefon raqamini kiriting:\n"
        "<i>(o'tkazib yuborish uchun - kiriting)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(SaleForm.add_customer_phone)
async def process_new_customer_phone(message: Message, state: FSMContext):
    import re

    data = await state.get_data()

    if message.text.strip() == "-":
        phone = None
    else:
        cleaned = re.sub(r"[\s\-\(\)]", "", message.text)
        if re.match(r"^\+?998\d{9}$", cleaned):
            phone = cleaned if cleaned.startswith("+") else f"+{cleaned}"
        elif re.match(r"^\d{9}$", cleaned):
            phone = f"+998{cleaned}"
        else:
            await message.answer(
                "❌ Noto'g'ri telefon formati!\n"
                "To'g'ri format: +998901234567 yoki 901234567",
            )
            return

    async with async_session() as session:
        from bot.schemas.customer import CustomerCreate
        customer_service = CustomerService(session)
        customer = await customer_service.create(
            CustomerCreate(name=data["new_customer_name"], phone=phone)
        )

        product_service = ProductService(session)
        products = await product_service.get_active()

    if not products:
        await state.clear()
        await message.answer(
            f"✅ Mijoz '{customer.name}' qo'shildi!\n\n"
            "❌ Lekin mahsulotlar mavjud emas.\n"
            "Avval mahsulot qo'shing.",
            reply_markup=main_menu(),
        )
        return

    available_products = {
        p.id: {"name": p.name, "price": float(p.price), "amount": p.amount, "unit": p.unit}
        for p in products
    }

    await state.update_data(
        customer_id=customer.id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_old_debt=0,
        products={},
        available_products=available_products,
    )
    await state.set_state(SaleForm.select_products)

    await message.answer(
        f"✅ Mijoz '{customer.name}' qo'shildi!\n\n"
        f"🛒 <b>Savdo</b> - {customer.name}\n\n"
        "📦 Mahsulot tanlang:",
        reply_markup=products_keyboard(available_products, {}),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.select_customer, F.data == "sale_search_customer")
async def sale_search_customer(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SaleForm.search_customer)
    await callback.message.edit_text(
        "🔍 <b>Mijoz qidirish</b>\n\n"
        "Mijoz ismi yoki telefon raqamini kiriting:\n"
        "<i>Masalan: Ali yoki 901234567</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(SaleForm.search_customer)
async def process_customer_search(message: Message, state: FSMContext):
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❌ Kamida 2 ta belgi kiriting:")
        return

    async with async_session() as session:
        customer_service = CustomerService(session)
        customers = await customer_service.search(query)

    if not customers:
        await message.answer(
            f"❌ '{query}' bo'yicha mijoz topilmadi.\n"
            "Qayta qidiring yoki yangi mijoz qo'shing:",
            reply_markup=sale_menu_keyboard(),
        )
        await state.set_state(SaleForm.select_customer)
        return

    buttons = []
    for c in customers:
        async with async_session() as session:
            cs = CustomerService(session)
            debt = await cs.get_debt(c.id)
        debt_str = f" 🔴 {int(debt):,}" if debt > 0 else ""
        buttons.append(
            [InlineKeyboardButton(text=f"{c.name}{debt_str}", callback_data=f"sale_customer_{c.id}")]
        )
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="sale_back_to_list")])

    await state.set_state(SaleForm.select_customer)
    await message.answer(
        f"🔍 <b>Qidiruv natijalari</b> ({len(customers)} ta):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "sale_back_to_list")
async def back_to_customer_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await start_sale(callback.message, state)


@router.callback_query(SaleForm.select_customer, F.data.startswith("sale_customer_"))
async def select_sale_customer(callback: CallbackQuery, state: FSMContext):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        customer_service = CustomerService(session)
        customer = await customer_service.get_by_id(customer_id)

        if not customer:
            await callback.answer("❌ Mijoz topilmadi", show_alert=True)
            return

        old_debt = await customer_service.get_debt(customer_id)

        product_service = ProductService(session)
        products = await product_service.get_active()

    if not products:
        await state.clear()
        await callback.message.edit_text(
            "❌ Mahsulotlar mavjud emas!\n"
            "📦 Mahsulotlar → ➕ Qo'shish"
        )
        return

    available_products = {
        p.id: {"name": p.name, "price": float(p.price), "amount": p.amount, "unit": p.unit}
        for p in products
    }

    await state.update_data(
        customer_id=customer_id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_old_debt=old_debt,
        products={},
        available_products=available_products,
    )
    await state.set_state(SaleForm.select_products)

    debt_info = ""
    if old_debt > 0:
        debt_info = f"\n⚠️ <b>Joriy qarz: {int(old_debt):,} so'm</b>\n"

    await callback.message.edit_text(
        f"🛒 <b>Savdo</b> - {customer.name}{debt_info}\n\n"
        "📦 Mahsulot tanlang:",
        reply_markup=products_keyboard(available_products, {}),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.select_products, F.data.startswith("sp_"))
async def handle_product_selection(callback: CallbackQuery, state: FSMContext):
    action = callback.data[3:]
    data = await state.get_data()
    products = data.get("products", {})
    available = data.get("available_products", {})

    if action == "done":
        if not products:
            await callback.answer("❌ Kamida bitta mahsulot tanlang!", show_alert=True)
            return

        total = sum(available[pid]["price"] * qty for pid, qty in products.items())

        product_lines = []
        for pid, qty in products.items():
            p = available[pid]
            subtotal = p["price"] * qty
            amount_str = format_amount(p["amount"], p["unit"])
            product_lines.append(
                f"  • {p['name']} ({amount_str}) x{qty} = {int(subtotal):,} so'm"
            )
        product_text = "\n".join(product_lines)

        await state.update_data(total_amount=total)
        await state.set_state(SaleForm.enter_paid)
        await callback.message.edit_text(
            f"🛒 <b>Tanlangan mahsulotlar:</b>\n{product_text}\n\n"
            f"💰 <b>Jami: {int(total):,} so'm</b>\n\n"
            "Naqd to'lov miqdorini kiriting:\n"
            "<i>(to'liq qarz uchun 0 kiriting)</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "clear":
        await state.update_data(products={})
        await callback.message.edit_reply_markup(
            reply_markup=products_keyboard(available, {})
        )
        await callback.answer("✅ Tozalandi")
        return

    # Mahsulot tanlash - son so'rash
    product_id = int(action)
    if product_id not in available:
        await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
        return

    p = available[product_id]
    await state.update_data(selecting_product=product_id)
    await state.set_state(SaleForm.enter_quantity)

    amount_str = format_amount(p["amount"], p["unit"])
    unit_emoji = "🥛" if p["unit"] == "l" else "⚖️"
    await callback.message.edit_text(
        f"📦 <b>{p['name']}</b>\n"
        f"💰 Narxi: {int(p['price']):,} so'm\n"
        f"{unit_emoji} Miqdori: {amount_str}\n\n"
        "Nechta olasiz?",
        reply_markup=quantity_keyboard(product_id),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.enter_quantity, F.data.startswith("qty_"))
async def handle_quantity_selection(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")

    if parts[1] == "back":
        data = await state.get_data()
        available = data.get("available_products", {})
        products = data.get("products", {})
        customer_name = data.get("customer_name", "")
        old_debt = data.get("customer_old_debt", 0)

        await state.set_state(SaleForm.select_products)

        debt_info = ""
        if old_debt > 0:
            debt_info = f"\n⚠️ <b>Joriy qarz: {int(old_debt):,} so'm</b>\n"

        await callback.message.edit_text(
            f"🛒 <b>Savdo</b> - {customer_name}{debt_info}\n\n"
            "📦 Mahsulot tanlang:",
            reply_markup=products_keyboard(available, products),
            parse_mode="HTML",
        )
        return

    product_id = int(parts[1])
    quantity = int(parts[2])

    data = await state.get_data()
    products = data.get("products", {})
    available = data.get("available_products", {})
    customer_name = data.get("customer_name", "")
    old_debt = data.get("customer_old_debt", 0)

    products[product_id] = products.get(product_id, 0) + quantity
    await state.update_data(products=products)
    await state.set_state(SaleForm.select_products)

    p = available[product_id]
    total = sum(available[pid]["price"] * qty for pid, qty in products.items())

    debt_info = ""
    if old_debt > 0:
        debt_info = f"\n⚠️ <b>Joriy qarz: {int(old_debt):,} so'm</b>\n"

    await callback.message.edit_text(
        f"🛒 <b>Savdo</b> - {customer_name}{debt_info}\n\n"
        f"✅ {p['name']} x{quantity} qo'shildi\n"
        f"💰 Jami: {int(total):,} so'm\n\n"
        "📦 Mahsulot tanlang:",
        reply_markup=products_keyboard(available, products),
        parse_mode="HTML",
    )


@router.message(SaleForm.enter_quantity)
async def handle_quantity_text(message: Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0 or quantity > 1000:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1 dan 1000 gacha son kiriting!")
        return

    data = await state.get_data()
    product_id = data.get("selecting_product")
    products = data.get("products", {})
    available = data.get("available_products", {})
    customer_name = data.get("customer_name", "")
    old_debt = data.get("customer_old_debt", 0)

    products[product_id] = products.get(product_id, 0) + quantity
    await state.update_data(products=products)
    await state.set_state(SaleForm.select_products)

    p = available[product_id]
    total = sum(available[pid]["price"] * qty for pid, qty in products.items())

    debt_info = ""
    if old_debt > 0:
        debt_info = f"\n⚠️ <b>Joriy qarz: {int(old_debt):,} so'm</b>\n"

    await message.answer(
        f"🛒 <b>Savdo</b> - {customer_name}{debt_info}\n\n"
        f"✅ {p['name']} x{quantity} qo'shildi\n"
        f"💰 Jami: {int(total):,} so'm\n\n"
        "📦 Mahsulot tanlang:",
        reply_markup=products_keyboard(available, products),
        parse_mode="HTML",
    )


@router.message(SaleForm.enter_paid)
async def process_paid_amount(message: Message, state: FSMContext):
    paid = parse_number(message.text)

    if paid is None or paid < 0:
        await message.answer(
            "❌ Noto'g'ri summa!\n"
            "Musbat son kiriting (masalan: 50000):"
        )
        return

    data = await state.get_data()
    total = data["total_amount"]
    old_debt = data.get("customer_old_debt", 0)

    if paid > total:
        if old_debt <= 0:
            await message.answer(
                f"❌ To'lov ({int(paid):,}) jami summadan ({int(total):,}) oshib ketdi!\n\n"
                "Qayta kiriting:",
            )
            return

        overpay = paid - total
        if overpay > old_debt:
            await message.answer(
                f"❌ Ortiqcha to'lov ({int(overpay):,}) qarzdan ({int(old_debt):,}) katta!\n\n"
                "Qayta kiriting:",
            )
            return

        await state.update_data(paid_amount=paid, overpay_amount=overpay)
        await state.set_state(SaleForm.handle_overpay)
        await message.answer(
            f"⚠️ <b>Ortiqcha to'lov</b>\n\n"
            f"Savdo summasi: {int(total):,} so'm\n"
            f"To'langan: {int(paid):,} so'm\n"
            f"Ortiqcha: {int(overpay):,} so'm\n\n"
            f"Mijozning joriy qarzi: {int(old_debt):,} so'm\n\n"
            "Ortiqchani qarzdan ayirishni xohlaysizmi?",
            reply_markup=overpay_keyboard(),
            parse_mode="HTML",
        )
        return

    debt = total - paid
    await state.update_data(paid_amount=paid, debt_amount=debt)

    products = data["products"]
    available = data["available_products"]

    product_lines = []
    for pid, qty in products.items():
        p = available[pid]
        subtotal = p["price"] * qty
        amount_str = format_amount(p["amount"], p["unit"])
        product_lines.append(
            f"  • {p['name']} ({amount_str}) x{qty} = {int(subtotal):,} so'm"
        )
    product_text = "\n".join(product_lines)

    total_debt = old_debt + debt

    await state.set_state(SaleForm.confirm)
    await message.answer(
        f"📋 <b>Savdo tafsilotlari:</b>\n\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"📞 Telefon: {data.get('customer_phone') or 'kiritilmagan'}\n\n"
        f"📦 <b>Mahsulotlar:</b>\n{product_text}\n\n"
        f"💰 Jami: {int(total):,} so'm\n"
        f"💵 Naqd: {int(paid):,} so'm\n"
        f"💳 Qarz: {int(debt):,} so'm\n"
        f"📊 Jami qarz: {int(total_debt):,} so'm\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.handle_overpay, F.data == "overpay_subtract")
async def handle_overpay_subtract(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data["total_amount"]
    paid = data["paid_amount"]
    overpay = data["overpay_amount"]
    old_debt = data.get("customer_old_debt", 0)
    products = data["products"]
    available = data["available_products"]

    new_debt = old_debt - overpay

    await state.update_data(
        paid_amount=total,
        debt_amount=0,
        subtract_from_debt=overpay,
        new_old_debt=new_debt,
    )

    product_lines = []
    for pid, qty in products.items():
        p = available[pid]
        subtotal = p["price"] * qty
        amount_str = format_amount(p["amount"], p["unit"])
        product_lines.append(
            f"  • {p['name']} ({amount_str}) x{qty} = {int(subtotal):,} so'm"
        )
    product_text = "\n".join(product_lines)

    await state.set_state(SaleForm.confirm)
    await callback.message.edit_text(
        f"📋 <b>Savdo tafsilotlari:</b>\n\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"📞 Telefon: {data.get('customer_phone') or 'kiritilmagan'}\n\n"
        f"📦 <b>Mahsulotlar:</b>\n{product_text}\n\n"
        f"💰 Jami: {int(total):,} so'm\n"
        f"💵 Naqd: {int(paid):,} so'm\n"
        f"💳 Bu savdo uchun qarz: 0 so'm\n"
        f"➖ Eski qarzdan ayiriladi: {int(overpay):,} so'm\n"
        f"📊 Yangi jami qarz: {int(new_debt):,} so'm\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.handle_overpay, F.data == "overpay_retry")
async def handle_overpay_retry(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data["total_amount"]

    await state.set_state(SaleForm.enter_paid)
    await callback.message.edit_text(
        f"💰 <b>Jami: {int(total):,} so'm</b>\n\n"
        "Naqd to'lov miqdorini qayta kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(SaleForm.confirm, F.data == "confirm")
async def confirm_sale(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    customer_id = data["customer_id"]
    customer_name = data["customer_name"]
    customer_phone = data.get("customer_phone")
    products = data["products"]
    available = data["available_products"]
    total = data["total_amount"]
    paid = data.get("paid_amount", 0)
    debt = data.get("debt_amount", 0)
    old_debt = data.get("customer_old_debt", 0)
    subtract_from_debt = data.get("subtract_from_debt", 0)

    sale_items = []
    products_data = []
    for pid, qty in products.items():
        p = available[pid]
        sale_items.append(
            SaleItemCreate(product_id=pid, quantity=qty, unit_price=p["price"])
        )
        products_data.append({
            "name": p["name"],
            "amount": p["amount"],
            "unit": p["unit"],
            "quantity": qty,
            "price": p["price"],
        })

    async with async_session() as session:
        sale_service = SaleService(session)
        sale = await sale_service.create(
            SaleCreate(
                customer_id=customer_id,
                total_amount=total,
                paid_amount=paid if subtract_from_debt == 0 else total,
                debt_amount=debt,
                items=sale_items,
            )
        )

        if subtract_from_debt > 0:
            payment_service = PaymentService(session)
            await payment_service.create(
                PaymentCreate(
                    customer_id=customer_id,
                    amount=subtract_from_debt,
                    note=f"Savdo #{sale.id} ortiqcha to'lovdan",
                )
            )

    receipt = generate_receipt(
        customer_name=customer_name,
        customer_phone=customer_phone,
        products_data=products_data,
        total=total,
        paid=paid,
        debt=debt,
        old_debt=old_debt - subtract_from_debt,
        sale_id=sale.id,
    )

    await state.clear()
    await callback.message.edit_text(receipt, parse_mode="HTML")
    await callback.message.answer(
        "🏠 Bosh menyu:",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi", reply_markup=main_menu())


# === TO'LOV ===

@router.message(F.text == "💰 To'lov")
async def start_payment(message: Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        customer_service = CustomerService(session)
        customers = await customer_service.get_all()

        customers_with_debt = []
        for c in customers:
            debt = await customer_service.get_debt(c.id)
            if debt > 0:
                customers_with_debt.append((c, debt))

    if not customers_with_debt:
        await message.answer(
            "✅ Barcha mijozlarning qarzi yo'q!",
            reply_markup=main_menu(),
        )
        return

    buttons = []
    for c, debt in customers_with_debt:
        buttons.append([
            InlineKeyboardButton(
                text=f"{c.name} - 🔴 {int(debt):,} so'm",
                callback_data=f"pay_customer_{c.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])

    await state.set_state(PaymentForm.select_customer)
    await message.answer(
        "💰 <b>Qarz to'lash</b>\n\n"
        "Mijozni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(PaymentForm.select_customer, F.data.startswith("pay_customer_"))
async def select_payment_customer(callback: CallbackQuery, state: FSMContext):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        customer_service = CustomerService(session)
        customer = await customer_service.get_by_id(customer_id)
        debt = await customer_service.get_debt(customer_id)

    if not customer:
        await callback.answer("❌ Mijoz topilmadi", show_alert=True)
        return

    await state.update_data(
        customer_id=customer_id,
        customer_name=customer.name,
        customer_debt=debt,
    )
    await state.set_state(PaymentForm.enter_amount)

    await callback.message.edit_text(
        f"💰 <b>Qarz to'lash</b>\n\n"
        f"👤 Mijoz: {customer.name}\n"
        f"💳 Joriy qarz: {int(debt):,} so'm\n\n"
        "To'lov miqdorini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(PaymentForm.enter_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    amount = parse_number(message.text)

    if amount is None or amount <= 0:
        await message.answer("❌ Musbat son kiriting!")
        return

    data = await state.get_data()
    debt = data["customer_debt"]

    if amount > debt:
        await message.answer(
            f"❌ To'lov ({int(amount):,}) qarzdan ({int(debt):,}) katta!\n"
            "Qayta kiriting:"
        )
        return

    await state.update_data(payment_amount=amount)
    await state.set_state(PaymentForm.confirm)

    remaining = debt - amount

    await message.answer(
        f"💰 <b>To'lov tafsilotlari:</b>\n\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"💳 Joriy qarz: {int(debt):,} so'm\n"
        f"💵 To'lov: {int(amount):,} so'm\n"
        f"📊 Qolgan qarz: {int(remaining):,} so'm\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(PaymentForm.confirm, F.data == "confirm")
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    async with async_session() as session:
        payment_service = PaymentService(session)
        await payment_service.create(
            PaymentCreate(
                customer_id=data["customer_id"],
                amount=data["payment_amount"],
            )
        )

        customer_service = CustomerService(session)
        remaining = await customer_service.get_debt(data["customer_id"])

    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>To'lov qabul qilindi!</b>\n\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"💵 To'landi: {int(data['payment_amount']):,} so'm\n"
        f"📊 Qolgan qarz: {int(remaining):,} so'm",
        parse_mode="HTML",
    )
    await callback.message.answer("🏠 Bosh menyu:", reply_markup=main_menu())
