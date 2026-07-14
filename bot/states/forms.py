from aiogram.fsm.state import State, StatesGroup


class ProductForm(StatesGroup):
    name = State()
    price = State()
    unit = State()  # gramm yoki litr
    amount = State()
    confirm = State()


class ProductEditForm(StatesGroup):
    waiting_field = State()
    name = State()
    price = State()
    unit = State()
    amount = State()


class CustomerForm(StatesGroup):
    name = State()
    phone = State()
    confirm = State()


class CustomerEditForm(StatesGroup):
    waiting_field = State()
    name = State()
    phone = State()


class CustomerSearchForm(StatesGroup):
    query = State()


class SaleForm(StatesGroup):
    select_customer = State()
    search_customer = State()
    add_customer_name = State()
    add_customer_phone = State()
    select_products = State()
    enter_quantity = State()
    enter_paid = State()
    handle_overpay = State()
    confirm = State()


class PaymentForm(StatesGroup):
    select_customer = State()
    enter_amount = State()
    enter_note = State()
    confirm = State()
