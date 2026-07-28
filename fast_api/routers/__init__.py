from fast_api.routers.packages import router as packages_router
from fast_api.routers.bookings import router as bookings_router
from fast_api.routers.payments import router as payments_router
from fast_api.routers.visa import router as visa_router
from fast_api.routers.flights import router as flights_router
from fast_api.routers.chatbot import router as chatbot_router
from fast_api.routers.bot_readonly import router as n8n_router

__all__ = [
    "packages_router",
    "bookings_router",
    "payments_router",
    "visa_router",
    "flights_router",
    "chatbot_router",
    "n8n_router",
]
