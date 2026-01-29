"""Prospect API endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from database.models import Prospect, Contact, ProspectScore, Activity
from api.schemas import (
    APIResponse, ProspectCreate, ProspectUpdate, ProspectRead,
    ProspectDetail, ContactRead, ProspectScoreRead, ActivityRead
)

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_prospects(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    state: Optional[str] = None,
    venue_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List prospects with optional filters."""
    query = db.query(Prospect).filter(Prospect.deleted_at.is_(None))

    if status:
        query = query.filter(Prospect.status == status)
    if tier:
        query = query.filter(Prospect.tier == tier)
    if state:
        query = query.filter(Prospect.state == state)
    if venue_type:
        query = query.filter(Prospect.venue_type == venue_type)
    if search:
        query = query.filter(Prospect.name.ilike(f"%{search}%"))

    total = query.count()
    prospects = query.order_by(Prospect.updated_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "prospects": [ProspectRead.model_validate(p) for p in prospects],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/stats", response_model=APIResponse)
async def get_prospect_stats(db: Session = Depends(get_db)):
    """Get pipeline statistics."""
    # Total prospects
    total = db.query(Prospect).filter(Prospect.deleted_at.is_(None)).count()

    # By status
    status_counts = (
        db.query(Prospect.status, func.count(Prospect.id))
        .filter(Prospect.deleted_at.is_(None))
        .group_by(Prospect.status)
        .all()
    )
    by_status = {status: count for status, count in status_counts}

    # By tier
    tier_counts = (
        db.query(Prospect.tier, func.count(Prospect.id))
        .filter(Prospect.deleted_at.is_(None), Prospect.tier.isnot(None))
        .group_by(Prospect.tier)
        .all()
    )
    by_tier = {tier: count for tier, count in tier_counts}

    return APIResponse(
        data={
            "total_prospects": total,
            "by_status": by_status,
            "by_tier": by_tier,
        }
    )


@router.get("/{prospect_id}", response_model=APIResponse)
async def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    """Get a single prospect with full details."""
    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id,
        Prospect.deleted_at.is_(None)
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    # Get related data
    contacts = db.query(Contact).filter(
        Contact.prospect_id == prospect_id,
        Contact.deleted_at.is_(None)
    ).all()

    scores = db.query(ProspectScore).filter(
        ProspectScore.prospect_id == prospect_id
    ).order_by(ProspectScore.scored_at.desc()).all()

    activities = db.query(Activity).filter(
        Activity.prospect_id == prospect_id
    ).order_by(Activity.created_at.desc()).limit(20).all()

    # Build response
    prospect_data = ProspectRead.model_validate(prospect)
    detail = ProspectDetail(
        **prospect_data.model_dump(),
        contacts=[ContactRead.model_validate(c) for c in contacts],
        scores=[ProspectScoreRead.model_validate(s) for s in scores],
        recent_activities=[ActivityRead.model_validate(a) for a in activities],
    )

    return APIResponse(data=detail)


@router.post("", response_model=APIResponse, status_code=201)
async def create_prospect(prospect: ProspectCreate, db: Session = Depends(get_db)):
    """Create a new prospect."""
    db_prospect = Prospect(**prospect.model_dump())
    db_prospect.status = "identified"

    db.add(db_prospect)
    db.commit()
    db.refresh(db_prospect)

    return APIResponse(data=ProspectRead.model_validate(db_prospect))


@router.patch("/{prospect_id}", response_model=APIResponse)
async def update_prospect(
    prospect_id: str,
    updates: ProspectUpdate,
    db: Session = Depends(get_db),
):
    """Update a prospect."""
    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id,
        Prospect.deleted_at.is_(None)
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prospect, field, value)

    db.commit()
    db.refresh(prospect)

    return APIResponse(data=ProspectRead.model_validate(prospect))


@router.delete("/{prospect_id}", response_model=APIResponse)
async def delete_prospect(prospect_id: str, db: Session = Depends(get_db)):
    """Soft delete a prospect."""
    from datetime import datetime

    prospect = db.query(Prospect).filter(
        Prospect.id == prospect_id,
        Prospect.deleted_at.is_(None)
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    prospect.deleted_at = datetime.utcnow()
    db.commit()

    return APIResponse(data={"deleted": True})
