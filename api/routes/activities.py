"""Activity API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.connection import get_db
from database.models import Activity, Prospect
from api.schemas import APIResponse, ActivityCreate, ActivityRead

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_activities(
    prospect_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List activities with optional filters."""
    query = db.query(Activity)

    if prospect_id:
        query = query.filter(Activity.prospect_id == prospect_id)
    if contact_id:
        query = query.filter(Activity.contact_id == contact_id)
    if type:
        query = query.filter(Activity.type == type)
    if since:
        query = query.filter(Activity.created_at >= since)

    total = query.count()
    activities = query.order_by(Activity.created_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "activities": [ActivityRead.model_validate(a) for a in activities],
            "total": total,
        }
    )


@router.get("/recent", response_model=APIResponse)
async def get_recent_activities(
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get recent activities across all prospects."""
    since = datetime.utcnow() - timedelta(hours=hours)

    activities = (
        db.query(Activity)
        .filter(Activity.created_at >= since)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .all()
    )

    return APIResponse(
        data=[ActivityRead.model_validate(a) for a in activities]
    )


@router.get("/{activity_id}", response_model=APIResponse)
async def get_activity(activity_id: str, db: Session = Depends(get_db)):
    """Get a single activity."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return APIResponse(data=ActivityRead.model_validate(activity))


@router.post("", response_model=APIResponse, status_code=201)
async def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    """Create a new activity."""
    # Verify prospect exists
    prospect = db.query(Prospect).filter(
        Prospect.id == activity.prospect_id,
        Prospect.deleted_at.is_(None)
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    db_activity = Activity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)

    return APIResponse(data=ActivityRead.model_validate(db_activity))
