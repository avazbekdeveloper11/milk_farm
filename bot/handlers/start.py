from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menus import (
    customers_menu,
    main_menu,
    products_menu,
    reports_menu,
)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
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
