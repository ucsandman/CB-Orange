"""Outreach management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database.connection import get_db
from database.models import OutreachSequence, OutreachTemplate, Prospect, Contact
from api.schemas import (
    APIResponse, OutreachSequenceRead, OutreachTemplateRead,
    PendingApproval, ProspectRead, ContactRead
)

router = APIRouter()


@router.get("/sequences", response_model=APIResponse)
async def list_sequences(
    prospect_id: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List outreach sequences with optional filters."""
    query = db.query(OutreachSequence)

    if prospect_id:
        query = query.filter(OutreachSequence.prospect_id == prospect_id)
    if status:
        query = query.filter(OutreachSequence.status == status)
    if tier:
        query = query.filter(OutreachSequence.tier == tier)

    total = query.count()
    sequences = query.order_by(OutreachSequence.created_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "sequences": [OutreachSequenceRead.model_validate(s) for s in sequences],
            "total": total,
        }
    )


@router.get("/sequences/{sequence_id}", response_model=APIResponse)
async def get_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """Get a single outreach sequence."""
    sequence = db.query(OutreachSequence).filter(OutreachSequence.id == sequence_id).first()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    return APIResponse(data=OutreachSequenceRead.model_validate(sequence))


@router.get("/pending-approvals", response_model=APIResponse)
async def get_pending_approvals(db: Session = Depends(get_db)):
    """Get all pending A1 approvals with full context."""
    sequences = (
        db.query(OutreachSequence)
        .filter(
            OutreachSequence.tier == 'A1',
            OutreachSequence.requires_approval == True,
            OutreachSequence.approved_at.is_(None),
            OutreachSequence.status.in_(['pending', 'active'])
        )
        .all()
    )

    approvals = []
    for seq in sequences:
        # Get prospect and contact
        prospect = db.query(Prospect).filter(Prospect.id == seq.prospect_id).first()
        contact = db.query(Contact).filter(Contact.id == seq.contact_id).first()

        if not prospect or not contact:
            continue

        # Get template for current step
        template = (
            db.query(OutreachTemplate)
            .filter(
                OutreachTemplate.tier == seq.tier,
                OutreachTemplate.step_number == seq.current_step + 1,  # Next step to send
                OutreachTemplate.is_active == True
            )
            .first()
        )

        if not template:
            continue

        # Build preview (in production, this would render variables)
        subject = template.subject_template
        body = template.body_template

        approvals.append(PendingApproval(
            sequence=OutreachSequenceRead.model_validate(seq),
            prospect=ProspectRead.model_validate(prospect),
            contact=ContactRead.model_validate(contact),
            email_subject=subject,
            email_body=body,
        ))

    return APIResponse(data=approvals)


@router.post("/sequences/{sequence_id}/approve", response_model=APIResponse)
async def approve_sequence(
    sequence_id: str,
    approved_by: str,
    db: Session = Depends(get_db),
):
    """Approve an A1 tier sequence for sending."""
    sequence = db.query(OutreachSequence).filter(OutreachSequence.id == sequence_id).first()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    if not sequence.requires_approval:
        raise HTTPException(status_code=400, detail="Sequence does not require approval")

    if sequence.approved_at:
        raise HTTPException(status_code=400, detail="Sequence already approved")

    sequence.approved_at = datetime.utcnow()
    sequence.approved_by = approved_by
    if sequence.status == 'pending':
        sequence.status = 'active'
        sequence.started_at = datetime.utcnow()

    db.commit()
    db.refresh(sequence)

    return APIResponse(data=OutreachSequenceRead.model_validate(sequence))


@router.post("/sequences/{sequence_id}/pause", response_model=APIResponse)
async def pause_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """Pause an active outreach sequence."""
    sequence = db.query(OutreachSequence).filter(OutreachSequence.id == sequence_id).first()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    if sequence.status != 'active':
        raise HTTPException(status_code=400, detail="Sequence is not active")

    sequence.status = 'paused'
    sequence.paused_at = datetime.utcnow()
    db.commit()
    db.refresh(sequence)

    return APIResponse(data=OutreachSequenceRead.model_validate(sequence))


@router.post("/sequences/{sequence_id}/resume", response_model=APIResponse)
async def resume_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """Resume a paused outreach sequence."""
    sequence = db.query(OutreachSequence).filter(OutreachSequence.id == sequence_id).first()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    if sequence.status != 'paused':
        raise HTTPException(status_code=400, detail="Sequence is not paused")

    sequence.status = 'active'
    sequence.paused_at = None
    db.commit()
    db.refresh(sequence)

    return APIResponse(data=OutreachSequenceRead.model_validate(sequence))


@router.post("/sequences/{sequence_id}/stop", response_model=APIResponse)
async def stop_sequence(sequence_id: str, db: Session = Depends(get_db)):
    """Stop an outreach sequence entirely."""
    sequence = db.query(OutreachSequence).filter(OutreachSequence.id == sequence_id).first()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    if sequence.status in ('completed', 'stopped'):
        raise HTTPException(status_code=400, detail="Sequence already finished")

    sequence.status = 'stopped'
    sequence.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(sequence)

    return APIResponse(data=OutreachSequenceRead.model_validate(sequence))


@router.get("/templates", response_model=APIResponse)
async def list_templates(
    tier: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List outreach templates."""
    query = db.query(OutreachTemplate)

    if tier:
        query = query.filter(OutreachTemplate.tier == tier)
    if active_only:
        query = query.filter(OutreachTemplate.is_active == True)

    templates = query.order_by(OutreachTemplate.tier, OutreachTemplate.step_number).all()

    return APIResponse(
        data=[OutreachTemplateRead.model_validate(t) for t in templates]
    )
