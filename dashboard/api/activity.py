"""
Activity feed API endpoints
Combines generation history and download events into unified feed
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
from pydantic import BaseModel
import uuid

from fastapi import APIRouter

router = APIRouter()

# In-memory activity store (max 50 items)
activity_store: deque = deque(maxlen=50)


class ActivityItem(BaseModel):
    """Single activity item"""
    id: str
    type: str  # generation, download
    status: str  # completed, failed, started
    title: str
    subtitle: str
    timestamp: str
    link: str


class ActivityResponse(BaseModel):
    """Response for activity list"""
    activities: List[ActivityItem]


def add_activity(
    activity_type: str,
    status: str,
    title: str,
    subtitle: str,
    link: str = "#"
) -> ActivityItem:
    """Add a new activity to the store"""
    activity = ActivityItem(
        id=f"{activity_type}_{uuid.uuid4().hex[:8]}",
        type=activity_type,
        status=status,
        title=title,
        subtitle=subtitle,
        timestamp=datetime.utcnow().isoformat() + "Z",
        link=link
    )
    activity_store.appendleft(activity)
    return activity


def get_activities(limit: int = 10) -> List[ActivityItem]:
    """Get recent activities"""
    return list(activity_store)[:limit]


def clear_activities():
    """Clear all activities"""
    activity_store.clear()


@router.get("/recent", response_model=ActivityResponse)
async def get_recent_activity(limit: int = 10):
    """Get recent activity feed combining generations and downloads"""
    from .presets import download_manager

    activities = list(activity_store)

    # Add current download as activity if active
    queue_status = download_manager.get_queue_status()
    if queue_status.get("current"):
        current = queue_status["current"]
        dl_activity = ActivityItem(
            id=f"dl_{current.get('preset_id', 'unknown')}",
            type="download",
            status="started",
            title=f"Downloading {current.get('preset_id', 'Model')}",
            subtitle=f"{current.get('progress', 0)}% complete",
            timestamp=datetime.utcnow().isoformat() + "Z",
            link=f"/models?preset={current.get('preset_id', '')}"
        )
        # Insert at beginning if not already there
        if not activities or activities[0].id != dl_activity.id:
            activities.insert(0, dl_activity)

    return ActivityResponse(activities=activities[:limit])


@router.delete("/clear")
async def clear_activity_history():
    """Clear all activity history"""
    clear_activities()
    return {"status": "success", "message": "Activity history cleared"}
