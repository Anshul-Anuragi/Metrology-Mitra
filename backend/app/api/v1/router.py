from fastapi import APIRouter
from app.api.v1.endpoints import analytics, auth, health, inspections, rules

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(rules.router, prefix="/rules", tags=["Legal Rules"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Supervisor Analytics"])
