# Oka Sut Mahsulotlari - Telegram Bot

## Loyiha maqsadi
Kichik sut fermasi uchun mahsulotlar, mijozlar va savdo/qarz hisobini yurituvchi Telegram bot.

---

## Texnologiyalar

| Texnologiya | Versiya | Maqsad |
|-------------|---------|--------|
| Python | 3.11+ | Asosiy til |
| aiogram | 3.x | Telegram Bot API |
| SQLAlchemy | 2.x | ORM (PostgreSQL'ga oson o'tish uchun) |
| SQLite | - | Dastlabki DB |
| Alembic | - | Migratsiyalar |
| Pydantic | 2.x | DTO va validatsiya |

---

## Database Schema

```
┌─────────────────────┐
│      products       │
├─────────────────────┤
│ id          INTEGER │ PK
│ name        TEXT    │ NOT NULL
│ price       REAL    │ NOT NULL (so'm)
│ weight_gram INTEGER │ NOT NULL
│ is_active   BOOLEAN │ DEFAULT TRUE
│ created_at  DATETIME│
│ updated_at  DATETIME│
└─────────────────────┘

┌─────────────────────┐
│      customers      │
├─────────────────────┤
│ id          INTEGER │ PK
│ name        TEXT    │ NOT NULL
│ phone       TEXT    │ UNIQUE
│ created_at  DATETIME│
│ updated_at  DATETIME│
└─────────────────────┘

┌─────────────────────┐
│       sales         │
├─────────────────────┤
│ id          INTEGER │ PK
│ customer_id INTEGER │ FK → customers
│ total_amount REAL   │ Jami summa
│ paid_amount  REAL   │ Naqd to'langan
│ debt_amount  REAL   │ Qarz (auto: total - paid)
│ created_at  DATETIME│
└─────────────────────┘

┌─────────────────────┐
│     sale_items      │
├─────────────────────┤
│ id          INTEGER │ PK
│ sale_id     INTEGER │ FK → sales
│ product_id  INTEGER │ FK → products
│ quantity    INTEGER │ Soni
│ unit_price  REAL    │ Sotilgan narx
│ subtotal    REAL    │ quantity × unit_price
└─────────────────────┘

┌─────────────────────┐
│      payments       │
├─────────────────────┤
│ id          INTEGER │ PK
│ customer_id INTEGER │ FK → customers
│ amount      REAL    │ To'lov summasi
│ note        TEXT    │ Izoh
│ created_at  DATETIME│
└─────────────────────┘
```

### Qarz hisoblash formulasi
```
Mijoz umumiy qarzi = SUM(sales.debt_amount) - SUM(payments.amount)
```

---

## Loyiha strukturasi (Clean Architecture)

```
sut_ferma_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Bot entry point
│   ├── config.py               # Settings (BOT_TOKEN, DB_URL)
│   │
│   ├── handlers/               # Telegram handlers (UI layer)
│   │   ├── __init__.py
│   │   ├── start.py            # /start, asosiy menu
│   │   ├── products.py         # Mahsulot CRUD
│   │   ├── customers.py        # Mijoz CRUD
│   │   ├── sales.py            # Savdo yaratish
│   │   └── reports.py          # Qarz hisoboti
│   │
│   ├── keyboards/              # Inline va Reply klaviaturalar
│   │   ├── __init__.py
│   │   └── menus.py
│   │
│   ├── states/                 # FSM states
│   │   ├── __init__.py
│   │   └── forms.py
│   │
│   ├── services/               # Business logic (Use Cases)
│   │   ├── __init__.py
│   │   ├── product_service.py
│   │   ├── customer_service.py
│   │   ├── sale_service.py
│   │   └── payment_service.py
│   │
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract repository
│   │   ├── product_repo.py
│   │   ├── customer_repo.py
│   │   ├── sale_repo.py
│   │   └── payment_repo.py
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model
│   │   ├── product.py
│   │   ├── customer.py
│   │   ├── sale.py
│   │   └── payment.py
│   │
│   ├── schemas/                # Pydantic DTOs
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── customer.py
│   │   └── sale.py
│   │
│   └── database/
│       ├── __init__.py
│       └── session.py          # DB session factory
│
├── alembic/                    # Migratsiyalar
│   └── versions/
│
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

## Bot funksionalligi

### Asosiy menu
```
🏠 Bosh menu
├── 📦 Mahsulotlar
│   ├── ➕ Qo'shish
│   ├── 📋 Ro'yxat
│   └── ✏️ Tahrirlash
│
├── 👥 Mijozlar
│   ├── ➕ Yangi mijoz
│   ├── 📋 Ro'yxat
│   └── 🔍 Qidirish
│
├── 🛒 Savdo
│   └── ➕ Yangi savdo (mijoz → mahsulotlar → naqd/qarz)
│
├── 💰 To'lovlar
│   └── ➕ Qarz to'lash
│
└── 📊 Hisobotlar
    ├── 📈 Bugungi savdo
    ├── 💳 Qarzlar ro'yxati
    └── 👤 Mijoz qarzi
```

### Savdo jarayoni (FSM)
1. Mijozni tanlash (ro'yxatdan yoki qidirish)
2. Mahsulotlarni tanlash (har biriga son kiritish)
3. Jami summa ko'rsatiladi
4. Naqd to'lov miqdorini kiritish
5. Qolgan qism avtomatik qarz bo'ladi
6. Tasdiqlash

---

## PostgreSQL'ga o'tish

SQLAlchemy ishlatilgani uchun faqat `config.py` da DB URL o'zgartirish kerak:

```python
# SQLite
DATABASE_URL = "sqlite:///./oka_sut.db"

# PostgreSQL
DATABASE_URL = "postgresql://user:pass@localhost/oka_sut"
```

---

## Ishga tushirish tartibi

1. Virtual environment yaratish
2. `pip install -r requirements.txt`
3. `.env` faylga `BOT_TOKEN` yozish
4. `alembic upgrade head` (migratsiyalar)
5. `python -m bot.main`

---

## Keyingi bosqichlar (ixtiyoriy)

- [ ] Excel export
- [ ] Kunlik/haftalik hisobotlar
- [ ] Admin foydalanuvchilar tizimi
- [ ] Mahsulot kategoriyalari

---

**Tasdiqlansinmi? Tasdiqlasangiz kod yozishni boshlayman.**
