from fastapi import APIRouter
from .endpoints import (
    auth, images, listings, telemetry, 
    price_suggestions, features, reviews, 
    disputes, contacts, analytics, categories, 
    chat, brands, devices, escrow, messages, 
    orders, payments, sync, maintenance

)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(images.router)
api_router.include_router(listings.router)
api_router.include_router(telemetry.router)
api_router.include_router(categories.router)
api_router.include_router(chat.router)
api_router.include_router(brands.router)
api_router.include_router(devices.router)
api_router.include_router(escrow.router)
api_router.include_router(messages.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(sync.router)
api_router.include_router(price_suggestions.router)
api_router.include_router(features.router)
api_router.include_router(reviews.router)
api_router.include_router(disputes.router)
api_router.include_router(contacts.router)
api_router.include_router(analytics.router)
api_router.include_router(maintenance.router)

