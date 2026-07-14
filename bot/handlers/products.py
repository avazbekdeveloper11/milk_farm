from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.session import async_session
from bot.keyboards.menus import (
    cancel_keyboard,
    confirm_keyboard,
    product_detail_keyboard,
    product_list_keyboard,
    products_menu,
)
from bot.schemas.product import ProductCreate, ProductUpdate
from bot.services.product_service import ProductService
from bot.states.forms import ProductForm, ProductEditForm

router = Router()


def parse_number(text: str, is_float: bool = False) -> float | int | None:
    try:
        cleaned = text.replace(",", "").replace(" ", "").strip()
        return float(cleaned) if is_float else int(cleaned)
    except ValueError:
        return None


def unit_keyboard() -> InlineKeyboardMarkup:
    """Birlik tanlash uchun tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="⚖️ Gramm (g)", callback_data="unit_g"),
            InlineKeyboardButton(text="🥛 Litr (l)", callback_data="unit_l"),
        ],
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


@router.callback_query(F.data == "product_add")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProductForm.name)
    await callback.message.edit_text(
        "📦 <b>Yangi mahsulot qo'shish</b>\n\n"
        "Mahsulot nomini kiriting:\n"
        "<i>Masalan: Kefir 1%</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProductForm.name)
async def process_product_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(
            "❌ Nom juda qisqa. Kamida 2 ta belgi kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    if len(name) > 100:
        await message.answer(
            "❌ Nom juda uzun. Maksimum 100 ta belgi:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(name=name)
    await state.set_state(ProductForm.price)
    await message.answer(
        "💰 Narxini kiriting (so'mda):\n"
        "<i>Masalan: 15000</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProductForm.price)
async def process_product_price(message: Message, state: FSMContext):
    price = parse_number(message.text, is_float=True)

    if price is None:
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "Faqat raqam kiriting.\n"
            "<i>Masalan: 15000</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    if price <= 0:
        await message.answer(
            "❌ Narx musbat bo'lishi kerak!",
            reply_markup=cancel_keyboard(),
        )
        return

    if price > 100_000_000:
        await message.answer(
            "❌ Narx juda katta!",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(price=price)
    await state.set_state(ProductForm.unit)
    await message.answer(
        "📏 <b>Birlik tanlang:</b>\n\n"
        "Mahsulot qanday o'lchovda?",
        reply_markup=unit_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(ProductForm.unit, F.data.startswith("unit_"))
async def process_product_unit(callback: CallbackQuery, state: FSMContext):
    unit = callback.data.split("_")[1]  # "g" yoki "l"
    await state.update_data(unit=unit)
    await state.set_state(ProductForm.amount)

    if unit == "l":
        await callback.message.edit_text(
            "🥛 <b>Hajmini kiriting (ml da):</b>\n"
            "<i>Masalan: 1000 (1 litr uchun)</i>\n"
            "<i>500 (0.5 litr uchun)</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            "⚖️ <b>Og'irligini kiriting (gramm da):</b>\n"
            "<i>Masalan: 500</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )


@router.message(ProductForm.amount)
async def process_product_amount(message: Message, state: FSMContext):
    amount = parse_number(message.text)

    if amount is None:
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "Faqat butun son kiriting.",
            reply_markup=cancel_keyboard(),
        )
        return

    if amount <= 0:
        await message.answer(
            "❌ Miqdor musbat bo'lishi kerak!",
            reply_markup=cancel_keyboard(),
        )
        return

    if amount > 100_000:
        await message.answer(
            "❌ Miqdor juda katta!",
            reply_markup=cancel_keyboard(),
        )
        return

    data = await state.get_data()
    await state.update_data(amount=amount)

    unit_text = format_amount(amount, data['unit'])
    unit_emoji = "🥛" if data['unit'] == "l" else "⚖️"

    await state.set_state(ProductForm.confirm)
    await message.answer(
        f"📋 <b>Tekshiring:</b>\n\n"
        f"📦 Nomi: {data['name']}\n"
        f"💰 Narxi: {int(data['price']):,} so'm\n"
        f"{unit_emoji} Miqdori: {unit_text}\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(ProductForm.confirm, F.data == "confirm")
async def confirm_add_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        service = ProductService(session)
        product = await service.create(
            ProductCreate(
                name=data["name"],
                price=data["price"],
                amount=data["amount"],
                unit=data["unit"],
            )
        )

    unit_text = format_amount(product.amount, product.unit)
    unit_emoji = "🥛" if product.unit == "l" else "⚖️"

    await callback.message.edit_text(
        f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
        f"📦 {product.name}\n"
        f"💰 {int(product.price):,} so'm\n"
        f"{unit_emoji} {unit_text}",
        parse_mode="HTML",
    )
    await callback.message.answer("📦 Mahsulotlar bo'limi:", reply_markup=products_menu())


@router.callback_query(F.data == "product_list")
async def show_product_list(callback: CallbackQuery):
    async with async_session() as session:
        service = ProductService(session)
        products = await service.get_active()

    if not products:
        await callback.message.edit_text(
            "📦 Mahsulotlar mavjud emas.\n"
            "Yangi mahsulot qo'shish uchun '➕ Qo'shish' tugmasini bosing.",
            reply_markup=products_menu(),
        )
    else:
        await callback.message.edit_text(
            f"📦 <b>Mahsulotlar ro'yxati</b> ({len(products)} ta):",
            reply_markup=product_list_keyboard(products),
            parse_mode="HTML",
        )


@router.callback_query(F.data.regexp(r"^product_(\d+)$"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        service = ProductService(session)
        product = await service.get_by_id(product_id)

    if not product:
        await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
        return

    unit_text = format_amount(product.amount, product.unit)
    unit_emoji = "🥛" if product.unit == "l" else "⚖️"

    await callback.message.edit_text(
        f"📦 <b>{product.name}</b>\n\n"
        f"💰 Narx: {int(product.price):,} so'm\n"
        f"{unit_emoji} Miqdor: {unit_text}\n"
        f"📌 Holat: {'✅ Faol' if product.is_active else '❌ Nofaol'}",
        reply_markup=product_detail_keyboard(product_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("product_delete_"))
async def delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        service = ProductService(session)
        product = await service.get_by_id(product_id)
        if product:
            await service.update(product_id, ProductUpdate(is_active=False))
            await callback.answer(f"✅ '{product.name}' o'chirildi", show_alert=True)
        else:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)

    await show_product_list(callback)


@router.callback_query(F.data.startswith("product_edit_"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        service = ProductService(session)
        product = await service.get_by_id(product_id)

    if not product:
        await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
        return

    await state.update_data(
        product_id=product_id,
        current_name=product.name,
        current_price=float(product.price),
        current_amount=product.amount,
        current_unit=product.unit,
    )
    await state.set_state(ProductEditForm.name)
    await callback.message.edit_text(
        f"✏️ <b>Mahsulotni tahrirlash</b>\n\n"
        f"Hozirgi nom: {product.name}\n\n"
        "Yangi nomni kiriting\n"
        "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProductEditForm.name)
async def edit_product_name(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.strip() == "-":
        new_name = None
    else:
        new_name = message.text.strip()
        if len(new_name) < 2:
            await message.answer("❌ Nom juda qisqa. Kamida 2 ta belgi:")
            return
        if len(new_name) > 100:
            await message.answer("❌ Nom juda uzun. Maksimum 100 ta belgi:")
            return

    await state.update_data(new_name=new_name)
    await state.set_state(ProductEditForm.price)
    await message.answer(
        f"Hozirgi narx: {int(data['current_price']):,} so'm\n\n"
        "Yangi narxni kiriting\n"
        "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProductEditForm.price)
async def edit_product_price(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.strip() == "-":
        new_price = None
    else:
        new_price = parse_number(message.text, is_float=True)
        if new_price is None:
            await message.answer("❌ Noto'g'ri format. Raqam kiriting:")
            return
        if new_price <= 0:
            await message.answer("❌ Narx musbat bo'lishi kerak!")
            return

    await state.update_data(new_price=new_price)
    await state.set_state(ProductEditForm.amount)

    unit_text = format_amount(data['current_amount'], data['current_unit'])
    await message.answer(
        f"Hozirgi miqdor: {unit_text}\n\n"
        "Yangi miqdorni kiriting\n"
        "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProductEditForm.amount)
async def edit_product_amount(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        new_amount = None
    else:
        new_amount = parse_number(message.text)
        if new_amount is None:
            await message.answer("❌ Noto'g'ri format. Butun son kiriting:")
            return
        if new_amount <= 0:
            await message.answer("❌ Miqdor musbat bo'lishi kerak!")
            return

    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        service = ProductService(session)
        product = await service.update(
            data["product_id"],
            ProductUpdate(
                name=data.get("new_name"),
                price=data.get("new_price"),
                amount=new_amount,
            ),
        )

    if product:
        unit_text = format_amount(product.amount, product.unit)
        unit_emoji = "🥛" if product.unit == "l" else "⚖️"
        await message.answer(
            f"✅ <b>Mahsulot yangilandi!</b>\n\n"
            f"📦 {product.name}\n"
            f"💰 {int(product.price):,} so'm\n"
            f"{unit_emoji} {unit_text}",
            parse_mode="HTML",
        )
        await message.answer("📦 Mahsulotlar bo'limi:", reply_markup=products_menu())
    else:
        await message.answer("❌ Xatolik yuz berdi", reply_markup=products_menu())


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi")

    if current_state and "Product" in current_state:
        await callback.message.answer("📦 Mahsulotlar bo'limi:", reply_markup=products_menu())
