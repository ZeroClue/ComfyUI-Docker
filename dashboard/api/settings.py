"""
Settings API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

from ..core.persistence import settings_manager

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    key: str
    value: str


class HFTokenUpdate(BaseModel):
    token: str


class SettingsResponse(BaseModel):
    theme: str
    hf_token_set: bool
    activity_retention_days: int


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings (token masked)"""
    return SettingsResponse(
        theme=settings_manager.get("theme") or "dark",
        hf_token_set=settings_manager.has_hf_token(),
        activity_retention_days=int(settings_manager.get("activity_retention_days") or "30")
    )


@router.patch("")
async def update_setting(update: SettingsUpdate):
    """Update a single setting"""
    valid_keys = ["theme", "hf_token", "activity_retention_days"]
    if update.key not in valid_keys:
        raise HTTPException(400, f"Invalid setting key: {update.key}")

    settings_manager.set(update.key, update.value)
    return {"status": "ok", "key": update.key}


@router.post("/hf-token")
async def set_hf_token(data: HFTokenUpdate):
    """Set HuggingFace token"""
    token = data.token.strip()
    if not token:
        raise HTTPException(400, "Token cannot be empty")

    # Validate token format (starts with hf_)
    if not token.startswith("hf_"):
        raise HTTPException(400, "Invalid token format. Token should start with 'hf_'")

    settings_manager.set("hf_token", token)
    return {"status": "ok", "message": "Token saved"}


@router.post("/hf-token/validate")
async def validate_hf_token():
    """Validate the current HF token"""
    token = settings_manager.get("hf_token")
    if not token:
        return {"valid": False, "error": "No token configured"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return {"valid": True, "username": data.get("name", "unknown")}
            else:
                return {"valid": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}


@router.delete("/hf-token")
async def delete_hf_token():
    """Delete the HF token"""
    settings_manager.delete("hf_token")
    return {"status": "ok", "message": "Token deleted"}
