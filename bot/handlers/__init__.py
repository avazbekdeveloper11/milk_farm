from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.products import router as products_router
from bot.handlers.customers import router as customers_router
from bot.handlers.sales import router as sales_router
from bot.handlers.reports import router as reports_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(products_router)
    router.include_router(customers_router)
    router.include_router(sales_router)
    router.include_router(reports_router)
    return router
