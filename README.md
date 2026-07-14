# SHOXZAMON MILK - Telegram Bot

Sut fermasi uchun mahsulotlar, mijozlar, savdo va qarz hisobini yurituvchi Telegram bot.

## Imkoniyatlar

- 📦 **Mahsulotlar**: qo'shish, ro'yxat, tahrirlash, o'chirish
- 👥 **Mijozlar**: qo'shish, qidirish, tahrirlash, qarz ko'rish
- 🛒 **Savdo**: mijoz tanlash → mahsulotlar → naqd/qarz taqsimoti
- 💰 **To'lov**: mijoz qarzini to'lash
- 📊 **Hisobotlar**: bugungi savdo, qarzlar ro'yxati

## Texnologiyalar

| Texnologiya | Versiya | Maqsad |
|-------------|---------|--------|
| Python | 3.11+ | Asosiy til |
| aiogram | 3.4 | Telegram Bot API |
| SQLAlchemy | 2.0 | ORM |
| SQLite/PostgreSQL | - | Ma'lumotlar bazasi |
| Pydantic | 2.5 | Validatsiya |

## O'rnatish

### 1. Repozitoriyani klonlash

```bash
git clone <repo-url>
cd sut_ferma_bot
```

### 2. Virtual environment yaratish

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# yoki
venv\Scripts\activate     # Windows
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. .env faylni sozlash

```bash
cp .env.example .env
```

`.env` faylni oching va quyidagilarni to'ldiring:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=sqlite+aiosqlite:///./oka_sut.db
```

**BOT_TOKEN olish:**
1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting (masalan: "SHOXZAMON MILK")
4. Bot username kiriting (masalan: "oka_sut_bot")
5. Berilgan tokenni `.env` faylga nusxalang

### 5. Botni ishga tushirish

```bash
python -m bot.main
```

Bot muvaffaqiyatli ishga tushganini ko'rasiz:
```
INFO:bot.main:Database tables created
INFO:bot.main:Bot started
```

## Foydalanish

### Asosiy menyular

Bot ishga tushgandan so'ng `/start` buyrug'ini yuboring:

```
🥛 SHOXZAMON MILKga xush kelibsiz!

📦 Mahsulotlar  👥 Mijozlar
🛒 Savdo        💰 To'lov
📊 Hisobotlar
```

### Savdo jarayoni

1. **🛒 Savdo** tugmasini bosing
2. Mijozni tanlang
3. Mahsulot raqami va sonini kiriting: `1 5` (1-mahsulotdan 5 ta)
4. `tayyor` yozing
5. Naqd to'lov miqdorini kiriting (qolgan qism avtomatik qarz bo'ladi)
6. Tasdiqlang

### Qarz to'lash

1. **💰 To'lov** tugmasini bosing
2. Qarzi bor mijozlardan birini tanlang
3. To'lov miqdorini kiriting
4. Tasdiqlang

## PostgreSQL'ga o'tish

1. PostgreSQL o'rnating va database yarating:

```sql
CREATE DATABASE oka_sut;
```

2. `asyncpg` kutubxonasini o'rnating:

```bash
pip install asyncpg
```

3. `.env` faylda `DATABASE_URL` ni o'zgartiring:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/oka_sut
```

4. Botni qayta ishga tushiring

## Testlarni ishga tushirish

```bash
# Barcha testlar
python -m pytest tests/ -v

# Integratsiya testlari
python -m pytest tests/test_full_flow.py -v -s
```

## Loyiha strukturasi

```
sut_ferma_bot/
├── bot/
│   ├── handlers/      # Telegram handlers
│   │   ├── start.py
│   │   ├── products.py
│   │   ├── customers.py
│   │   ├── sales.py
│   │   └── reports.py
│   ├── keyboards/     # Inline va Reply klaviaturalar
│   ├── states/        # FSM states
│   ├── services/      # Business logic
│   ├── repositories/  # Data access layer
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic DTOs
│   ├── database/      # DB session
│   ├── config.py
│   └── main.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Qarz hisoblash formulasi

```
Mijoz qarzi = SUM(savdo qarzlari) - SUM(to'lovlar)
```

## Xavfsizlik

- `.env` faylni git'ga qo'shmang
- `BOT_TOKEN` ni hech kimga bermang
- Production'da `DEBUG=False` qiling

## Muallif

SHOXZAMON MILK © 2024
