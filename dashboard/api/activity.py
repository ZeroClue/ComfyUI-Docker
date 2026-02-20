"""
Activity API endpoints - persisted to database
"""

from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel

from ..core import persistence

router = APIRouter(prefix="/activity", tags=["activity"])


def get_activity_logger():
    """Get activity logger at runtime (after init_persistence has run)"""
    return persistence.activity_logger


class ActivityItem(BaseModel):
    id: int
    type: str
    status: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    details: Optional[dict] = None
    created_at: str


class ActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total: int


def add_activity(
    activity_type: str,
    status: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    details: Optional[dict] = None
):
    """Add an activity to the log (used by other modules)"""
    if get_activity_logger():
        get_activity_logger().log(
            activity_type=activity_type,
            status=status,
            title=title,
            subtitle=subtitle,
            details=details
        )


@router.get("/recent", response_model=ActivityResponse)
async def get_recent_activity(limit: int = 20, activity_type: Optional[str] = None):
    """Get recent activity from database"""
    activities = get_activity_logger().get_recent(limit=limit, activity_type=activity_type)
    return ActivityResponse(
        activities=[ActivityItem(**a) for a in activities],
        total=len(activities)
    )


@router.post("/clear")
async def clear_activity():
    """Clear all activity history"""
    count = get_activity_logger().clear()
    return {"status": "ok", "deleted": count}
