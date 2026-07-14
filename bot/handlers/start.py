from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.config import settings
from bot.database.session import async_session
from bot.keyboards.menus import (
    cancel_keyboard,
    customers_menu,
    main_menu,
    products_menu,
    reports_menu,
    settings_menu,
)
from bot.models.user import AuthorizedUser
from bot.states.forms import AuthForm, ChangePasswordForm

router = Router()


async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🥛 <b>SHOXZAMON MILK</b>ga xush kelibsiz!\n\n"
        "🏪 <b>Tabiiy sut mahsulotlari ishlab chiqaruvchi</b>\n"
        "📱 <b>Bot imkoniyatlari:</b>\n"
        "📦 Mahsulotlar - qo'shish, tahrirlash, narxlar\n"
        "👥 Mijozlar - ro'yxat, qarz hisobi\n"
        "🛒 Savdo - tez va qulay savdo qilish\n"
        "💰 To'lov - qarzlarni qabul qilish\n"
        "📊 Hisobotlar - kunlik savdo, qarzlar\n\n"
        "📞 <b>Bog'lanish:</b>\n"
        "☎️ +998 88 951 51 14\n"
        "☎️ +998 88 280 51 14\n\n"
        "📢 <b>Kanallarimiz:</b>\n"
        "🔹 @SHOXZAMONMILK\n"
        "🔹 @TABIIYSUT\n"
        "👇 Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, is_authorized: bool = False):
    await state.clear()

    if is_authorized:
        await show_main_menu(message, state)
        return

    await state.set_state(AuthForm.waiting_password)
    await message.answer(
        "🔐 <b>Kirish</b>\n\n"
        "Botdan foydalanish uchun parolni kiriting:",
        parse_mode="HTML",
    )


@router.message(AuthForm.waiting_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()

    if password == settings.admin_password:
        async with async_session() as session:
            user = AuthorizedUser(telegram_id=message.from_user.id)
            session.add(user)
            await session.commit()

        await message.answer("✅ Muvaffaqiyatli kirdingiz!")
        await show_main_menu(message, state)
    else:
        await message.answer(
            "❌ Noto'g'ri parol!\n\n"
            "Qaytadan urinib ko'ring:",
            parse_mode="HTML",
        )


@router.message(F.text.lower().contains("sozlama"))
async def show_settings_menu(message: Message, state: FSMContext, is_authorized: bool = False):
    if not is_authorized:
        await message.answer("❌ Siz tizimga kirmagansiz. /start buyrug'ini bosing.")
        return
    await state.clear()
    await message.answer("⚙️ Sozlamalar:", reply_markup=settings_menu())


@router.callback_query(F.data == "change_password")
async def start_change_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangePasswordForm.current_password)
    await callback.message.edit_text(
        "🔐 <b>Parolni o'zgartirish</b>\n\n"
        "Joriy parolni kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ChangePasswordForm.current_password)
async def process_current_password(message: Message, state: FSMContext):
    if message.text.strip() != settings.admin_password:
        await message.answer(
            "❌ Joriy parol noto'g'ri!\n\n"
            "Qaytadan kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.set_state(ChangePasswordForm.new_password)
    await message.answer(
        "Yangi parolni kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(ChangePasswordForm.new_password)
async def process_new_password(message: Message, state: FSMContext):
    new_password = message.text.strip()

    if len(new_password) < 4:
        await message.answer(
            "❌ Parol kamida 4 ta belgidan iborat bo'lishi kerak!\n\n"
            "Yangi parolni kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(new_password=new_password)
    await state.set_state(ChangePasswordForm.confirm_password)
    await message.answer(
        "Yangi parolni tasdiqlash uchun qayta kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(ChangePasswordForm.confirm_password)
async def process_confirm_password(message: Message, state: FSMContext):
    data = await state.get_data()
    new_password = data.get("new_password")
    confirm = message.text.strip()

    if new_password != confirm:
        await message.answer(
            "❌ Parollar mos kelmadi!\n\n"
            "Yangi parolni qayta kiriting:",
            reply_markup=cancel_keyboard(),
        )
        await state.set_state(ChangePasswordForm.new_password)
        return

    settings.admin_password = new_password
    await state.clear()
    await message.answer(
        f"✅ Parol muvaffaqiyatli o'zgartirildi!\n\n"
        f"🔐 Yangi parol: <code>{new_password}</code>",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Yordam</b>\n\n"
        "📦 <b>Mahsulotlar</b> - mahsulot qo'shish, ro'yxat, tahrirlash\n"
        "👥 <b>Mijozlar</b> - mijoz qo'shish, qidirish, qarz ko'rish\n"
        "🛒 <b>Savdo</b> - yangi savdo yaratish\n"
        "💰 <b>To'lov</b> - qarz to'lash\n"
        "📊 <b>Hisobotlar</b> - bugungi savdo, qarzlar\n\n"
        "/start - bosh menyu\n"
        "/help - yordam",
        parse_mode="HTML",
    )


@router.message(F.text.lower().contains("mahsulot"))
async def show_products_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📦 Mahsulotlar bo'limi:", reply_markup=products_menu())


@router.message(F.text.lower().contains("mijoz"))
async def show_customers_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👥 Mijozlar bo'limi:", reply_markup=customers_menu())


@router.message(F.text.lower().contains("hisobot"))
async def show_reports_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📊 Hisobotlar bo'limi:", reply_markup=reports_menu())


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("📦 Mahsulotlar bo'limi:", reply_markup=products_menu())


@router.callback_query(F.data == "back_customers")
async def back_to_customers(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("👥 Mijozlar bo'limi:", reply_markup=customers_menu())
