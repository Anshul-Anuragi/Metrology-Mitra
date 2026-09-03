from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics,
    auth,
    batches,
    enforcement,
    exemptions,
    gravimetric,
    health,
    inspections,
    provenance,
    rules,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(rules.router, prefix="/rules", tags=["Legal Rules"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
api_router.include_router(batches.router, prefix="/batches", tags=["Batch Inspections"])
api_router.include_router(enforcement.router, prefix="/enforcement", tags=["Enforcement & Compounding"])
api_router.include_router(gravimetric.router, prefix="/gravimetric", tags=["Physical Metrology & MPE"])
api_router.include_router(exemptions.router, prefix="/exemptions", tags=["Statutory Exemptions & Special Packaging"])
api_router.include_router(provenance.router, prefix="/provenance", tags=["Field Geofence & Provenance"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Supervisor Analytics"])
