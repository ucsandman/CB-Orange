"""Contact API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Contact, Prospect
from api.schemas import APIResponse, ContactCreate, ContactUpdate, ContactRead

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_contacts(
    prospect_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List contacts with optional filters."""
    query = db.query(Contact).filter(Contact.deleted_at.is_(None))

    if prospect_id:
        query = query.filter(Contact.prospect_id == prospect_id)
    if search:
        query = query.filter(
            (Contact.name.ilike(f"%{search}%")) |
            (Contact.email.ilike(f"%{search}%"))
        )

    total = query.count()
    contacts = query.order_by(Contact.is_primary.desc(), Contact.name).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "contacts": [ContactRead.model_validate(c) for c in contacts],
            "total": total,
        }
    )


@router.get("/{contact_id}", response_model=APIResponse)
async def get_contact(contact_id: str, db: Session = Depends(get_db)):
    """Get a single contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None)
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return APIResponse(data=ContactRead.model_validate(contact))


@router.post("", response_model=APIResponse, status_code=201)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact."""
    # Verify prospect exists
    prospect = db.query(Prospect).filter(
        Prospect.id == contact.prospect_id,
        Prospect.deleted_at.is_(None)
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)

    return APIResponse(data=ContactRead.model_validate(db_contact))


@router.patch("/{contact_id}", response_model=APIResponse)
async def update_contact(
    contact_id: str,
    updates: ContactUpdate,
    db: Session = Depends(get_db),
):
    """Update a contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None)
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return APIResponse(data=ContactRead.model_validate(contact))


@router.delete("/{contact_id}", response_model=APIResponse)
async def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    """Soft delete a contact."""
    from datetime import datetime

    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None)
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.deleted_at = datetime.utcnow()
    db.commit()

    return APIResponse(data={"deleted": True})
