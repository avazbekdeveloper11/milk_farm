from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.database.session import async_session
from bot.keyboards.menus import customer_select_keyboard, reports_menu
from bot.services.customer_service import CustomerService
from bot.services.sale_service import SaleService

router = Router()


@router.callback_query(F.data == "report_today")
async def show_today_report(callback: CallbackQuery):
    async with async_session() as session:
        service = SaleService(session)
        stats = await service.get_today_stats()

    if stats["count"] == 0:
        await callback.message.edit_text(
            "📈 <b>Kunlik savdo hisoboti</b>\n\n"
            "Bugun hali savdo amalga oshirilmagan.",
            reply_markup=reports_menu(),
            parse_mode="HTML",
        )
        return

    profit_rate = (stats["paid"] / stats["total"] * 100) if stats["total"] > 0 else 0

    await callback.message.edit_text(
        f"📈 <b>Kunlik savdo hisoboti</b>\n\n"
        f"🛒 Savdolar soni: {stats['count']}\n"
        f"💰 Jami summa: {int(stats['total']):,} so'm\n"
        f"💵 Naqd to'langan: {int(stats['paid']):,} so'm\n"
        f"💳 Qarzga berilgan: {int(stats['debt']):,} so'm\n\n"
        f"📊 To'lov ulushi: {profit_rate:.1f}%",
        reply_markup=reports_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "report_monthly")
async def show_monthly_report(callback: CallbackQuery):
    async with async_session() as session:
        service = SaleService(session)
        stats = await service.get_monthly_stats()

    if stats["count"] == 0:
        await callback.message.edit_text(
            "📅 <b>Oylik savdo hisoboti</b>\n\n"
            "Bu oyda hali savdo amalga oshirilmagan.",
            reply_markup=reports_menu(),
            parse_mode="HTML",
        )
        return

    profit_rate = (stats["paid"] / stats["total"] * 100) if stats["total"] > 0 else 0

    await callback.message.edit_text(
        f"📅 <b>Oylik savdo hisoboti</b>\n\n"
        f"🛒 Savdolar soni: {stats['count']}\n"
        f"💰 Jami summa: {int(stats['total']):,} so'm\n"
        f"💵 Naqd to'langan: {int(stats['paid']):,} so'm\n"
        f"💳 Qarzga berilgan: {int(stats['debt']):,} so'm\n\n"
        f"📊 To'lov ulushi: {profit_rate:.1f}%",
        reply_markup=reports_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "report_yearly")
async def show_yearly_report(callback: CallbackQuery):
    async with async_session() as session:
        service = SaleService(session)
        stats = await service.get_yearly_stats()

    if stats["count"] == 0:
        await callback.message.edit_text(
            "📆 <b>Yillik savdo hisoboti</b>\n\n"
            "Bu yilda hali savdo amalga oshirilmagan.",
            reply_markup=reports_menu(),
            parse_mode="HTML",
        )
        return

    profit_rate = (stats["paid"] / stats["total"] * 100) if stats["total"] > 0 else 0

    await callback.message.edit_text(
        f"📆 <b>Yillik savdo hisoboti</b>\n\n"
        f"🛒 Savdolar soni: {stats['count']}\n"
        f"💰 Jami summa: {int(stats['total']):,} so'm\n"
        f"💵 Naqd to'langan: {int(stats['paid']):,} so'm\n"
        f"💳 Qarzga berilgan: {int(stats['debt']):,} so'm\n\n"
        f"📊 To'lov ulushi: {profit_rate:.1f}%",
        reply_markup=reports_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "report_debts")
async def show_debts_report(callback: CallbackQuery):
    async with async_session() as session:
        customer_service = CustomerService(session)
        customers = await customer_service.get_all()

        debts = []
        total_debt = 0
        for customer in customers:
            debt = await customer_service.get_debt(customer.id)
            if debt > 0:
                debts.append((customer.name, customer.phone, debt))
                total_debt += debt

    if not debts:
        await callback.message.edit_text(
            "💳 <b>Qarzlar hisoboti</b>\n\n"
            "✅ Hech kimning qarzi yo'q!",
            reply_markup=reports_menu(),
            parse_mode="HTML",
        )
        return

    debts.sort(key=lambda x: x[2], reverse=True)

    debt_lines = []
    for i, (name, phone, debt) in enumerate(debts[:20], 1):
        phone_str = f" ({phone})" if phone else ""
        debt_lines.append(f"{i}. {name}{phone_str}: {int(debt):,} so'm")

    debt_text = "\n".join(debt_lines)

    extra = ""
    if len(debts) > 20:
        extra = f"\n<i>... va yana {len(debts) - 20} ta mijoz</i>"

    await callback.message.edit_text(
        f"💳 <b>Qarzlar hisoboti</b>\n\n"
        f"{debt_text}{extra}\n\n"
        f"👥 Qarzdorlar soni: {len(debts)}\n"
        f"📊 <b>Jami qarz: {int(total_debt):,} so'm</b>",
        reply_markup=reports_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "report_customer")
async def start_customer_report(callback: CallbackQuery):
    async with async_session() as session:
        customer_service = CustomerService(session)
        customers = await customer_service.get_all()

    if not customers:
        await callback.answer("Mijozlar mavjud emas", show_alert=True)
        return

    await callback.message.edit_text(
        "📊 <b>Mijoz hisoboti</b>\n\n"
        "Mijozni tanlang:",
        reply_markup=customer_select_keyboard(customers, "report"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("report_customer_"))
async def show_customer_report(callback: CallbackQuery):
    customer_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        customer_service = CustomerService(session)
        customer = await customer_service.get_by_id(customer_id)

        if not customer:
            await callback.answer("Mijoz topilmadi", show_alert=True)
            return

        debt = await customer_service.get_debt(customer_id)

    debt_status = "🟢 Qarz yo'q" if debt <= 0 else f"🔴 {int(debt):,} so'm qarz"

    await callback.message.edit_text(
        f"📊 <b>Mijoz hisoboti</b>\n\n"
        f"👤 Ism: {customer.name}\n"
        f"📞 Telefon: {customer.phone or 'Kiritilmagan'}\n"
        f"💳 Holat: {debt_status}",
        reply_markup=reports_menu(),
        parse_mode="HTML",
    )
