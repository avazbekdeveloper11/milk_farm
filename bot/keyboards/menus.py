from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.models.customer import Customer
from bot.models.product import Product


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📦 Mahsulotlar"), KeyboardButton(text="👥 Mijozlar")],
        [KeyboardButton(text="🛒 Savdo"), KeyboardButton(text="💰 To'lov")],
        [KeyboardButton(text="📊 Hisobotlar"), KeyboardButton(text="⚙️ Sozlamalar")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def settings_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔐 Parolni o'zgartirish", callback_data="change_password")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Qo'shish", callback_data="product_add")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="product_list")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def customers_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Yangi mijoz", callback_data="customer_add")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="customer_list")],
        [InlineKeyboardButton(text="🔍 Qidirish", callback_data="customer_search")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def reports_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📈 Kunlik savdo", callback_data="report_today")],
        [InlineKeyboardButton(text="📅 Oylik savdo", callback_data="report_monthly")],
        [InlineKeyboardButton(text="📆 Yillik savdo", callback_data="report_yearly")],
        [InlineKeyboardButton(text="💳 Qarzlar ro'yxati", callback_data="report_debts")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_list_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        text = f"{p.name} - {int(p.price):,} so'm"
        buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"product_{p.id}")]
        )
    buttons.append(
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_products")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Tahrirlash", callback_data=f"product_edit_{product_id}"
            ),
            InlineKeyboardButton(
                text="🗑 O'chirish", callback_data=f"product_delete_{product_id}"
            ),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="product_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def customer_list_keyboard(customers: list[Customer]) -> InlineKeyboardMarkup:
    buttons = []
    for c in customers:
        text = f"{c.name}" + (f" ({c.phone})" if c.phone else "")
        buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"customer_{c.id}")]
        )
    buttons.append(
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_customers")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def customer_detail_keyboard(customer_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="💳 Qarzini ko'rish", callback_data=f"customer_debt_{customer_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Tahrirlash", callback_data=f"customer_edit_{customer_id}"
            ),
            InlineKeyboardButton(
                text="🗑 O'chirish", callback_data=f"customer_delete_{customer_id}"
            ),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="customer_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def customer_select_keyboard(
    customers: list[Customer], action: str = "sale"
) -> InlineKeyboardMarkup:
    buttons = []
    for c in customers:
        text = f"{c.name}" + (f" ({c.phone})" if c.phone else "")
        buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"{action}_customer_{c.id}")]
        )
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
