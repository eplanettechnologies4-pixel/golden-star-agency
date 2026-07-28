from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fast_api.config import settings
from fast_api.routers import (
    packages_router,
    bookings_router,
    payments_router,
    visa_router,
    flights_router,
    chatbot_router,
    n8n_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="FastAPI service for bookings, payments, and AI chatbot in Golden Star Agency"
)

# CORS configurations - Allow requests from the Django server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production (e.g. ['http://localhost:8000'])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(packages_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(visa_router)
app.include_router(flights_router)
app.include_router(chatbot_router)
app.include_router(n8n_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }
