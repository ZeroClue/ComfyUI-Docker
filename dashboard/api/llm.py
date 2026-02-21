"""
LLM API endpoints
Handles prompt enhancement and model management.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.llm_service import llm_service, LLM_MODELS


# Request/Response Models
class EnhanceRequest(BaseModel):
    """Request for prompt enhancement."""
    prompt: str = Field(..., description="Prompt to enhance")
    style: str = Field("detailed", description="Enhancement style")
    model: str = Field("phi-3-mini", description="Model to use")


class EnhanceResponse(BaseModel):
    """Response for prompt enhancement."""
    success: bool
    original_prompt: str
    enhanced_prompt: Optional[str] = None
    style: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


class DownloadRequest(BaseModel):
    """Request to download a model."""
    model_id: str = Field(..., description="Model ID to download")


class DownloadResponse(BaseModel):
    """Response for model download."""
    success: bool
    message: str
    path: Optional[str] = None
    error: Optional[str] = None


# Initialize router
router = APIRouter()


@router.get("/status")
async def get_llm_status():
    """Get LLM service status and installed models."""
    return llm_service.get_status()


@router.get("/models")
async def list_available_models():
    """List all available LLM models."""
    return {
        "models": [
            {
                "id": model_id,
                "name": config["name"],
                "size_gb": config["size_gb"],
                "installed": llm_service.is_installed(model_id),
            }
            for model_id, config in LLM_MODELS.items()
        ]
    }


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_prompt(request: EnhanceRequest) -> EnhanceResponse:
    """
    Enhance a prompt using the local LLM.

    Requires LLM to be enabled and model installed.
    """
    # Check if model is installed
    if not llm_service.is_installed(request.model):
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model} not installed. Download it first."
        )

    result = await llm_service.enhance_prompt(
        prompt=request.prompt,
        style=request.style,
        model_id=request.model
    )

    return EnhanceResponse(**result)


@router.post("/download", response_model=DownloadResponse)
async def download_model(request: DownloadRequest) -> DownloadResponse:
    """
    Download an LLM model.

    Models are stored in /workspace/models/llm/{model_id}/
    """
    if request.model_id not in LLM_MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {request.model_id}")

    result = await llm_service.download_model(request.model_id)
    return DownloadResponse(**result)


__all__ = ["router"]
