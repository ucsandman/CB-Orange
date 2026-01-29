"""Import API endpoints for uploading JSON from Claude skills."""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from api.schemas import APIResponse
from api.import_service import import_json_file, detect_skill_type
from api.import_schemas import ImportResult

router = APIRouter()


@router.post("/upload", response_model=APIResponse)
async def upload_json_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a JSON file from a Claude skill.

    Accepts JSON files from:
    - athletic-director-prospecting skill
    - contact-finder-enrichment skill

    The skill type is auto-detected from the file contents.
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="File must be a JSON file"
        )

    # Read and parse JSON
    try:
        contents = await file.read()
        json_data = json.loads(contents.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )

    # Import the data
    try:
        result = import_json_file(db, json_data)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

    return APIResponse(
        success=result.success,
        data={
            "skill_type": result.skill_type,
            "prospects_created": result.prospects_created,
            "prospects_updated": result.prospects_updated,
            "contacts_created": result.contacts_created,
            "contacts_updated": result.contacts_updated,
            "imported_ids": result.imported_ids,
            "errors": result.errors,
            "warnings": result.warnings,
        },
        error=result.errors[0] if result.errors and not result.success else None
    )


@router.post("/json", response_model=APIResponse)
async def import_json_data(
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Import JSON data directly (not as file upload).

    Accepts JSON body from:
    - athletic-director-prospecting skill
    - contact-finder-enrichment skill

    The skill type is auto-detected from the data.
    """
    try:
        result = import_json_file(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

    return APIResponse(
        success=result.success,
        data={
            "skill_type": result.skill_type,
            "prospects_created": result.prospects_created,
            "prospects_updated": result.prospects_updated,
            "contacts_created": result.contacts_created,
            "contacts_updated": result.contacts_updated,
            "imported_ids": result.imported_ids,
            "errors": result.errors,
            "warnings": result.warnings,
        },
        error=result.errors[0] if result.errors and not result.success else None
    )


@router.post("/preview", response_model=APIResponse)
async def preview_import(
    file: UploadFile = File(...),
):
    """Preview what an import would do without actually importing.

    Returns information about what records would be created/updated.
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="File must be a JSON file"
        )

    # Read and parse JSON
    try:
        contents = await file.read()
        json_data = json.loads(contents.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {str(e)}"
        )

    # Detect skill type and extract preview info
    try:
        skill_type = detect_skill_type(json_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    preview = {
        "skill_type": skill_type,
        "file_name": file.filename,
    }

    if skill_type == "athletic-director-prospecting":
        prospects = json_data.get("prospects", [])
        preview["prospect_count"] = len(prospects)
        preview["prospects"] = [
            {
                "name": p.get("institution", {}).get("name"),
                "type": p.get("institution", {}).get("type"),
                "state": p.get("institution", {}).get("state"),
                "tier": p.get("scoring", {}).get("tier") if p.get("scoring") else None,
                "icp_score": p.get("scoring", {}).get("icp_score") if p.get("scoring") else None,
                "has_decision_maker": bool(p.get("decision_maker", {}).get("name")),
                "secondary_contacts_count": len(p.get("secondary_contacts", [])),
            }
            for p in prospects
        ]
    elif skill_type == "contact-finder-enrichment":
        enriched = json_data.get("enriched_prospects", [])
        preview["prospect_count"] = len(enriched)
        preview["prospects"] = [
            {
                "institution": p.get("institution"),
                "tier": p.get("tier"),
                "total_score": p.get("total_score"),
                "contacts_count": len(p.get("contacts", [])),
            }
            for p in enriched
        ]
    elif skill_type == "contact-finder":
        contacts = json_data.get("contacts", [])
        preview["prospect_count"] = len(contacts)
        preview["prospects"] = [
            {
                "institution": p.get("institution"),
                "tier": p.get("tier"),
                "total_score": p.get("score"),
                "contacts_count": (1 if p.get("primary_contact") else 0) + len(p.get("secondary_contacts", [])),
            }
            for p in contacts
        ]
    elif skill_type == "contact-finder-prospects":
        prospects = json_data.get("prospects", [])
        preview["prospect_count"] = len(prospects)
        preview["prospects"] = [
            {
                "institution": p.get("institution"),
                "tier": p.get("tier"),
                "total_score": p.get("score"),
                "contacts_count": (
                    (1 if p.get("contacts", {}).get("primary_decision_maker") else 0) +
                    len(p.get("contacts", {}).get("secondary_contacts", []))
                ),
            }
            for p in prospects
        ]
    else:
        # Fallback for unknown types - return empty prospects list
        preview["prospect_count"] = 0
        preview["prospects"] = []

    return APIResponse(data=preview)
