from fastapi import APIRouter

from app.api.routes.compare import router as compare_router
from app.api.routes.estimate import router as estimate_router
from app.api.routes.health import router as health_router
from app.api.routes.recommendations import router as recommendations_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(estimate_router, tags=["estimation"])
api_router.include_router(recommendations_router, tags=["recommendations"])
api_router.include_router(compare_router, tags=["comparison"])

