"""
API Router initialization for ComfyUI Unified Dashboard
Aggregates all API endpoint modules
"""

from fastapi import APIRouter

from .presets import router as presets_router
from .models import router as models_router
from .workflows import router as workflows_router
from .system import router as system_router
from .activity import router as activity_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(presets_router, prefix="/presets", tags=["presets"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(activity_router, prefix="/activity", tags=["activity"])


__all__ = ["api_router"]
