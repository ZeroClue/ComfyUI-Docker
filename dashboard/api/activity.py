"""
Activity API endpoints - persisted to database
"""

from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel

from ..core.persistence import activity_logger

router = APIRouter(prefix="/activity", tags=["activity"])


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
    if activity_logger:
        activity_logger.log(
            activity_type=activity_type,
            status=status,
            title=title,
            subtitle=subtitle,
            details=details
        )


@router.get("/recent", response_model=ActivityResponse)
async def get_recent_activity(limit: int = 20, activity_type: Optional[str] = None):
    """Get recent activity from database"""
    activities = activity_logger.get_recent(limit=limit, activity_type=activity_type)
    return ActivityResponse(
        activities=[ActivityItem(**a) for a in activities],
        total=len(activities)
    )


@router.post("/clear")
async def clear_activity():
    """Clear all activity history"""
    count = activity_logger.clear()
    return {"status": "ok", "deleted": count}
