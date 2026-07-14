import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.session import async_session
from bot.keyboards.menus import (
    cancel_keyboard,
    confirm_keyboard,
    customer_detail_keyboard,
    customer_list_keyboard,
    customers_menu,
)
from bot.schemas.customer import CustomerCreate, CustomerUpdate
from bot.services.customer_service import CustomerService
from bot.states.forms import CustomerForm, CustomerEditForm, CustomerSearchForm

router = Router()


def validate_phone(phone: str) -> str | None:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if re.match(r"^\+?998\d{9}$", cleaned):
        return cleaned
    if re.match(r"^\d{9}$", cleaned):
        return f"+998{cleaned}"
    return None


@router.callback_query(F.data == "customer_add")
async def start_add_customer(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CustomerForm.name)
    await callback.message.edit_text(
        "👤 <b>Yangi mijoz qo'shish</b>\n\n"
        "Mijoz ismini kiriting:\n"
        "<i>Masalan: Ali Valiyev</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CustomerForm.name)
async def process_customer_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❌ Ism juda qisqa. Kamida 2 ta belgi kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    if len(name) > 100:
        await message.answer(
            "❌ Ism juda uzun. Maksimum 100 ta belgi:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(name=name)
    await state.set_state(CustomerForm.phone)
    await message.answer(
        "📞 Telefon raqamini kiriting:\n"
        "<i>Masalan: +998901234567 yoki 901234567</i>\n\n"
        "<i>(o'tkazib yuborish uchun - kiriting)</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CustomerForm.phone)
async def process_customer_phone(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.strip() == "-":
        phone = None
    else:
        phone = validate_phone(message.text)
        if phone is None:
            await message.answer(
                "❌ Noto'g'ri telefon formati!\n"
                "To'g'ri format: +998901234567 yoki 901234567\n\n"
                "<i>(o'tkazib yuborish uchun - kiriting)</i>",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML",
            )
            return

    await state.update_data(phone=phone)
    await state.set_state(CustomerForm.confirm)

    await message.answer(
        f"📋 <b>Tekshiring:</b>\n\n"
        f"👤 Ism: {data['name']}\n"
        f"📞 Telefon: {phone or 'Kiritilmagan'}\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(CustomerForm.confirm, F.data == "confirm")
async def confirm_add_customer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        service = CustomerService(session)
        customer = await service.create(
            CustomerCreate(name=data["name"], phone=data.get("phone"))
        )

    await callback.message.edit_text(
        f"✅ <b>Mijoz qo'shildi!</b>\n\n"
        f"👤 {customer.name}\n"
        f"📞 {customer.phone or 'Kiritilmagan'}",
        parse_mode="HTML",
    )
    await callback.message.answer("👥 Mijozlar bo'limi:", reply_markup=customers_menu())


@router.callback_query(F.data == "customer_list")
async def show_customer_list(callback: CallbackQuery):
    async with async_session() as session:
        service = CustomerService(session)
        customers = await service.get_all()

    if not customers:
        await callback.message.edit_text(
            "👥 Mijozlar mavjud emas.\n"
            "Yangi mijoz qo'shish uchun '➕ Yangi mijoz' tugmasini bosing.",
            reply_markup=customers_menu(),
        )
    else:
        await callback.message.edit_text(
            f"👥 <b>Mijozlar ro'yxati</b> ({len(customers)} ta):",
            reply_markup=customer_list_keyboard(customers),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "customer_search")
async def start_search_customer(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CustomerSearchForm.query)
    await callback.message.edit_text(
        "🔍 <b>Mijoz qidirish</b>\n\n"
        "Mijoz ismi yoki telefon raqamini kiriting:\n"
        "<i>Masalan: Ali yoki 901234567</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CustomerSearchForm.query)
async def process_search_customer(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()

    if len(query) < 2:
        await message.answer(
            "❌ Qidiruv so'zi juda qisqa. Kamida 2 ta belgi kiriting.",
            reply_markup=customers_menu(),
        )
        return

    async with async_session() as session:
        service = CustomerService(session)
        customers = await service.search(query)

    if not customers:
        await message.answer(
            f"🔍 '<b>{query}</b>' bo'yicha mijoz topilmadi.",
            reply_markup=customers_menu(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"🔍 <b>Qidiruv natijalari</b> ({len(customers)} ta):",
            reply_markup=customer_list_keyboard(customers),
            parse_mode="HTML",
        )


@router.callback_query(F.data.regexp(r"^customer_(\d+)$"))
async def show_customer_detail(callback: CallbackQuery):
    customer_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        service = CustomerService(session)
        customer = await service.get_by_id(customer_id)

        if not customer:
            await callback.answer("❌ Mijoz topilmadi", show_alert=True)
            return

        debt = await service.get_debt(customer_id)

    debt_status = "🟢 Qarz yo'q" if debt <= 0 else f"🔴 {int(debt):,} so'm"

    await callback.message.edit_text(
        f"👤 <b>{customer.name}</b>\n\n"
        f"📞 Telefon: {customer.phone or 'Kiritilmagan'}\n"
        f"💳 Qarz: {debt_status}",
        reply_markup=customer_detail_keyboard(customer_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("customer_debt_"))
async def show_customer_debt(callback: CallbackQuery):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        service = CustomerService(session)
        customer = await service.get_by_id(customer_id)

        if not customer:
            await callback.answer("❌ Mijoz topilmadi", show_alert=True)
            return

        debt = await service.get_debt(customer_id)

    if debt <= 0:
        await callback.answer(f"✅ {customer.name}ning qarzi yo'q", show_alert=True)
    else:
        await callback.answer(
            f"💳 {customer.name} qarzi: {int(debt):,} so'm",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("customer_delete_"))
async def delete_customer(callback: CallbackQuery):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        service = CustomerService(session)
        customer = await service.get_by_id(customer_id)

        if not customer:
            await callback.answer("❌ Mijoz topilmadi", show_alert=True)
            return

        debt = await service.get_debt(customer_id)
        if debt > 0:
            await callback.answer(
                f"❌ Bu mijozning {int(debt):,} so'm qarzi bor. O'chirib bo'lmaydi!",
                show_alert=True,
            )
            return

        name = customer.name
        await service.delete(customer_id)

    await callback.answer(f"✅ '{name}' o'chirildi", show_alert=True)
    await show_customer_list(callback)


@router.callback_query(F.data.startswith("customer_edit_"))
async def start_edit_customer(callback: CallbackQuery, state: FSMContext):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        service = CustomerService(session)
        customer = await service.get_by_id(customer_id)

    if not customer:
        await callback.answer("❌ Mijoz topilmadi", show_alert=True)
        return

    await state.update_data(
        customer_id=customer_id,
        current_name=customer.name,
        current_phone=customer.phone,
    )
    await state.set_state(CustomerEditForm.name)
    await callback.message.edit_text(
        f"✏️ <b>Mijozni tahrirlash</b>\n\n"
        f"Hozirgi ism: {customer.name}\n\n"
        "Yangi ismni kiriting\n"
        "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CustomerEditForm.name)
async def edit_customer_name(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text.strip() == "-":
        new_name = None
    else:
        new_name = message.text.strip()
        if len(new_name) < 2:
            await message.answer("❌ Ism juda qisqa. Kamida 2 ta belgi:")
            return
        if len(new_name) > 100:
            await message.answer("❌ Ism juda uzun. Maksimum 100 ta belgi:")
            return

    await state.update_data(new_name=new_name)
    await state.set_state(CustomerEditForm.phone)
    await message.answer(
        f"Hozirgi telefon: {data['current_phone'] or 'Kiritilmagan'}\n\n"
        "Yangi telefon raqamini kiriting\n"
        "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(CustomerEditForm.phone)
async def edit_customer_phone(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        new_phone = None
    else:
        new_phone = validate_phone(message.text)
        if new_phone is None and message.text.strip() != "-":
            await message.answer(
                "❌ Noto'g'ri telefon formati!\n"
                "To'g'ri format: +998901234567\n\n"
                "<i>(o'zgarishsiz qoldirish uchun - kiriting)</i>",
                parse_mode="HTML",
            )
            return

    data = await state.get_data()
    await state.clear()

    update_data = {}
    if data.get("new_name"):
        update_data["name"] = data["new_name"]
    if new_phone:
        update_data["phone"] = new_phone

    async with async_session() as session:
        service = CustomerService(session)
        if update_data:
            customer = await service.update(
                data["customer_id"],
                CustomerUpdate(**update_data),
            )
        else:
            customer = await service.get_by_id(data["customer_id"])

    if customer:
        await message.answer(
            f"✅ <b>Mijoz yangilandi!</b>\n\n"
            f"👤 {customer.name}\n"
            f"📞 {customer.phone or 'Kiritilmagan'}",
            parse_mode="HTML",
        )
        await message.answer("👥 Mijozlar bo'limi:", reply_markup=customers_menu())
    else:
        await message.answer("❌ Xatolik yuz berdi", reply_markup=customers_menu())
