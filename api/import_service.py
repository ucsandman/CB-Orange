"""Service for importing JSON data from Claude skills into the pipeline."""
import json
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from database.models import (
    Prospect, Contact, ProspectScore, Activity, AgentAuditLog,
    VENUE_TYPES, STATES, TIERS
)
from api.import_schemas import (
    AthleticDirectorImport, ContactFinderImport, ImportResult,
    ProspectDiscoveryData, EnrichedProspect, EnrichedContact,
    ContactFinderDirectImport, ContactFinderProspect
)


def detect_skill_type(data: dict) -> str:
    """Detect the skill type from JSON data."""
    skill_type = data.get("skill_type", "")
    if skill_type == "athletic-director-prospecting":
        return "athletic-director-prospecting"
    elif skill_type == "contact-finder-enrichment":
        return "contact-finder-enrichment"
    elif skill_type == "contact-finder":
        return "contact-finder"
    elif "prospects" in data:
        return "athletic-director-prospecting"
    elif "enriched_prospects" in data:
        return "contact-finder-enrichment"
    elif "contacts" in data and isinstance(data.get("contacts"), list):
        # Check if it looks like contact-finder format
        if data["contacts"] and "institution" in data["contacts"][0]:
            return "contact-finder"
    raise ValueError("Unknown skill type - cannot determine import format")


def map_institution_type_to_venue_type(inst_type: str) -> str:
    """Map institution type from skill to our venue_type enum."""
    inst_type_lower = inst_type.lower()

    if "division i " in inst_type_lower or "d1" in inst_type_lower:
        return "college_d1"
    elif "division ii" in inst_type_lower or "d2" in inst_type_lower:
        return "college_d2"
    elif "division iii" in inst_type_lower or "d3" in inst_type_lower:
        return "college_d3"
    elif "naia" in inst_type_lower:
        return "college_naia"
    elif "6a" in inst_type_lower or "class 6" in inst_type_lower:
        return "high_school_6a"
    elif "5a" in inst_type_lower or "class 5" in inst_type_lower:
        return "high_school_5a"
    elif "4a" in inst_type_lower or "class 4" in inst_type_lower:
        return "high_school_4a"
    elif "3a" in inst_type_lower or "class 3" in inst_type_lower:
        return "high_school_3a"
    elif "high school" in inst_type_lower:
        return "high_school_5a"  # Default for unclassified high schools
    elif "college" in inst_type_lower or "university" in inst_type_lower:
        return "college_d2"  # Default for unclassified colleges
    else:
        return "high_school_other"


def map_state(state: Optional[str]) -> str:
    """Map state to our allowed states."""
    if not state:
        return "OTHER"
    state_upper = state.upper()
    if state_upper in STATES:
        return state_upper
    return "OTHER"


def map_tier(tier: Optional[str]) -> Optional[str]:
    """Map tier to our tier enum."""
    if not tier:
        return None
    tier_upper = tier.upper()
    if tier_upper in TIERS:
        return tier_upper
    return None


def map_lighting_type(lighting_str: Optional[str]) -> Optional[str]:
    """Map lighting description to our lighting type."""
    if not lighting_str:
        return "unknown"

    lighting_lower = lighting_str.lower()
    if "metal halide" in lighting_lower:
        return "metal_halide"
    elif "led" in lighting_lower:
        if "early" in lighting_lower or "old" in lighting_lower or "2002" in lighting_lower:
            return "early_led"
        else:
            return "modern_led"
    elif "unknown" in lighting_lower or "aging" in lighting_lower:
        return "unknown"
    else:
        return "unknown"


def map_broadcast_requirements(broadcast_capable: Optional[bool], notes: Optional[str] = None) -> str:
    """Map broadcast capability to our broadcast requirements."""
    if broadcast_capable is True:
        return "local_streaming"
    elif broadcast_capable is False:
        return "none"
    return "none"


def map_contact_role(authority_level: Optional[str], role_in_decision: Optional[str]) -> str:
    """Map authority/role to our contact role."""
    if authority_level:
        auth_lower = authority_level.lower()
        if auth_lower == "high":
            return "decision_maker"
        elif auth_lower == "medium":
            return "influencer"
        elif auth_lower == "low":
            return "influencer"

    if role_in_decision:
        role_lower = role_in_decision.lower()
        if "approval" in role_lower or "final" in role_lower or "primary" in role_lower:
            return "decision_maker"
        elif "budget" in role_lower or "technical" in role_lower:
            return "influencer"
        elif "gatekeeper" in role_lower:
            return "blocker"

    return "unknown"


def calculate_status_from_tier(tier: Optional[str], has_research: bool) -> str:
    """Determine pipeline status based on tier and research completeness."""
    if not tier:
        return "needs_scoring"

    if tier in ("A1", "A2"):
        if has_research:
            return "ready_for_outreach"
        return "needs_research"
    elif tier == "B":
        return "scored"  # B tier goes to nurture track
    elif tier in ("C", "D"):
        return "deprioritized"

    return "scored"


def import_athletic_director_prospects(db: Session, data: AthleticDirectorImport) -> ImportResult:
    """Import prospects from athletic-director-prospecting skill."""
    result = ImportResult(
        success=True,
        skill_type="athletic-director-prospecting"
    )

    for prospect_data in data.prospects:
        try:
            # Check for existing prospect by name
            existing = db.query(Prospect).filter(
                Prospect.name == prospect_data.institution.name,
                Prospect.deleted_at.is_(None)
            ).first()

            # Build research notes from various fields
            research_notes_parts = []
            if prospect_data.deal_risk_flags:
                research_notes_parts.append("Risk Flags:\n- " + "\n- ".join(prospect_data.deal_risk_flags))
            if prospect_data.sales_readiness:
                if prospect_data.sales_readiness.key_assumptions:
                    research_notes_parts.append("Key Assumptions:\n- " + "\n- ".join(prospect_data.sales_readiness.key_assumptions))
                if prospect_data.sales_readiness.required_validation:
                    research_notes_parts.append("Required Validation:\n- " + "\n- ".join(prospect_data.sales_readiness.required_validation))
            if prospect_data.outreach and prospect_data.outreach.timing_triggers:
                research_notes_parts.append("Timing Triggers:\n- " + "\n- ".join(prospect_data.outreach.timing_triggers))

            research_notes = "\n\n".join(research_notes_parts) if research_notes_parts else None

            # Determine if we have research
            has_research = bool(
                prospect_data.facility_hypothesis and
                prospect_data.facility_hypothesis.statement
            )

            tier = map_tier(prospect_data.scoring.tier if prospect_data.scoring else None)

            prospect_dict = {
                "name": prospect_data.institution.name,
                "venue_type": map_institution_type_to_venue_type(prospect_data.institution.type),
                "state": map_state(prospect_data.institution.state),
                "city": prospect_data.institution.city,
                "conference": prospect_data.institution.conference,
                "enrollment": prospect_data.institution.enrollment,
                "stadium_name": prospect_data.facility.primary_venue if prospect_data.facility else None,
                "current_lighting_type": map_lighting_type(
                    prospect_data.facility.current_lighting if prospect_data.facility else None
                ),
                "current_lighting_age_years": (
                    prospect_data.facility.lighting_age_years if prospect_data.facility else None
                ),
                "broadcast_requirements": map_broadcast_requirements(
                    prospect_data.facility.broadcast_capable if prospect_data.facility else None
                ),
                "tier": tier,
                "icp_score": prospect_data.scoring.icp_score if prospect_data.scoring else None,
                "constraint_hypothesis": (
                    prospect_data.facility_hypothesis.statement
                    if prospect_data.facility_hypothesis else None
                ),
                "value_proposition": (
                    prospect_data.sales_readiness.opportunity_summary
                    if prospect_data.sales_readiness else None
                ),
                "research_notes": research_notes,
                "source": "skill_import",
                "source_date": datetime.utcnow().date(),
            }

            if existing:
                # Update existing prospect
                for key, value in prospect_dict.items():
                    if value is not None:  # Only update non-null values
                        setattr(existing, key, value)
                existing.status = calculate_status_from_tier(tier, has_research)
                existing.updated_at = datetime.utcnow()
                prospect = existing
                result.prospects_updated += 1
            else:
                # Create new prospect
                prospect = Prospect(**prospect_dict)
                prospect.status = calculate_status_from_tier(tier, has_research)
                db.add(prospect)
                db.flush()  # Get the ID
                result.prospects_created += 1

            result.imported_ids.append(prospect.id)

            # Import primary decision maker as contact
            if prospect_data.decision_maker and prospect_data.decision_maker.name:
                dm = prospect_data.decision_maker
                existing_contact = db.query(Contact).filter(
                    Contact.prospect_id == prospect.id,
                    Contact.email == dm.email,
                    Contact.deleted_at.is_(None)
                ).first() if dm.email else None

                if not existing_contact:
                    contact = Contact(
                        prospect_id=prospect.id,
                        name=dm.name,
                        title=dm.title,
                        role=map_contact_role(dm.authority_level, None),
                        email=dm.email,
                        phone=dm.phone,
                        linkedin_url=dm.linkedin_url,
                        is_primary=True,
                        notes=dm.notes,
                    )
                    db.add(contact)
                    result.contacts_created += 1

            # Import secondary contacts
            if prospect_data.secondary_contacts:
                for sc in prospect_data.secondary_contacts:
                    existing_contact = db.query(Contact).filter(
                        Contact.prospect_id == prospect.id,
                        Contact.email == sc.email,
                        Contact.deleted_at.is_(None)
                    ).first() if sc.email else None

                    if not existing_contact:
                        contact = Contact(
                            prospect_id=prospect.id,
                            name=sc.name,
                            title=sc.title,
                            role=map_contact_role(None, sc.role_in_decision),
                            email=sc.email,
                            phone=sc.phone,
                            is_primary=False,
                            notes=sc.role_in_decision,
                        )
                        db.add(contact)
                        result.contacts_created += 1

            # Create activity for import
            activity = Activity(
                prospect_id=prospect.id,
                type="note",
                description=f"Imported from athletic-director-prospecting skill",
                agent_id="import_service",
            )
            db.add(activity)

            # Store ICP scores if available
            if prospect_data.scoring and prospect_data.scoring.score_breakdown:
                _import_scores(db, prospect.id, prospect_data.scoring)

        except Exception as e:
            result.errors.append(f"Error importing {prospect_data.institution.name}: {str(e)}")
            result.success = False

    db.commit()
    return result


def _import_scores(db: Session, prospect_id: str, scoring) -> None:
    """Import ICP dimension scores."""
    # Map skill scoring dimensions to our dimensions
    dimension_map = {
        "facility_condition": ("current_lighting_age", 3),
        "institution_size": ("venue_type", 2),
        "budget_signals": ("budget_signals", 3),
        "decision_maker_access": ("decision_maker_access", 2),
        "timing_triggers": ("project_timeline", 3),
        "geographic_fit": ("geography", 2),
        "competitive_pressure": ("night_game_frequency", 2),
        "purchase_readiness": ("broadcast_requirements", 2),
    }

    if not scoring.score_breakdown:
        return

    for skill_dim, (our_dim, default_weight) in dimension_map.items():
        if skill_dim in scoring.score_breakdown:
            breakdown = scoring.score_breakdown[skill_dim]
            score_val = breakdown.get("score", 5)
            weight_val = breakdown.get("weight", default_weight)

            # Check for existing score
            existing = db.query(ProspectScore).filter(
                ProspectScore.prospect_id == prospect_id,
                ProspectScore.dimension == our_dim
            ).first()

            if not existing:
                score = ProspectScore(
                    prospect_id=prospect_id,
                    dimension=our_dim,
                    score=min(10, max(1, score_val)),
                    weight=min(5, max(1, weight_val)),
                    notes=f"Imported from skill ({skill_dim})",
                    scored_by="agent:import",
                )
                db.add(score)


def import_contact_finder_enrichment(db: Session, data: ContactFinderImport) -> ImportResult:
    """Import contacts from contact-finder-enrichment skill."""
    result = ImportResult(
        success=True,
        skill_type="contact-finder-enrichment"
    )

    for enriched in data.enriched_prospects:
        try:
            # Find existing prospect by institution name
            prospect = db.query(Prospect).filter(
                Prospect.name == enriched.institution,
                Prospect.deleted_at.is_(None)
            ).first()

            if not prospect:
                # Try fuzzy match on name
                prospect = db.query(Prospect).filter(
                    Prospect.name.ilike(f"%{enriched.institution}%"),
                    Prospect.deleted_at.is_(None)
                ).first()

            if not prospect:
                result.warnings.append(
                    f"Prospect not found for institution: {enriched.institution}. "
                    "Import the athletic-director-prospecting file first."
                )
                continue

            result.imported_ids.append(prospect.id)

            # Update tier/score if provided
            if enriched.tier and not prospect.tier:
                prospect.tier = map_tier(enriched.tier)
            if enriched.total_score and not prospect.icp_score:
                prospect.icp_score = enriched.total_score

            # Determine primary contact from outreach sequence
            primary_contact_name = None
            if enriched.recommended_outreach_sequence:
                first_in_sequence = next(
                    (item for item in enriched.recommended_outreach_sequence if item.order == 1),
                    None
                )
                if first_in_sequence:
                    primary_contact_name = first_in_sequence.contact

            # Import contacts
            for contact_data in enriched.contacts:
                # Skip low-confidence contacts
                if contact_data.confidence and contact_data.confidence < 70:
                    continue

                # Check for existing contact by email
                existing_contact = None
                if contact_data.email:
                    existing_contact = db.query(Contact).filter(
                        Contact.prospect_id == prospect.id,
                        Contact.email == contact_data.email,
                        Contact.deleted_at.is_(None)
                    ).first()

                is_primary = (
                    primary_contact_name and
                    contact_data.name.lower() == primary_contact_name.lower()
                )

                contact_dict = {
                    "name": contact_data.name,
                    "title": contact_data.title,
                    "role": map_contact_role(contact_data.authority_level, contact_data.role_in_decision),
                    "email": contact_data.email,
                    "phone": contact_data.phone or contact_data.cell,
                    "linkedin_url": contact_data.linkedin_url,
                    "is_primary": is_primary,
                    "notes": contact_data.notes,
                }

                if existing_contact:
                    # Update existing contact
                    for key, value in contact_dict.items():
                        if value is not None:
                            setattr(existing_contact, key, value)
                    existing_contact.updated_at = datetime.utcnow()
                    result.contacts_updated += 1
                else:
                    # Create new contact
                    contact = Contact(
                        prospect_id=prospect.id,
                        **contact_dict
                    )
                    db.add(contact)
                    result.contacts_created += 1

            # Create activity for enrichment
            activity = Activity(
                prospect_id=prospect.id,
                type="note",
                description=f"Contacts enriched from contact-finder skill ({len(enriched.contacts)} contacts)",
                agent_id="import_service",
            )
            db.add(activity)

        except Exception as e:
            result.errors.append(f"Error enriching {enriched.institution}: {str(e)}")
            result.success = False

    db.commit()
    return result


def import_contact_finder_direct(db: Session, data: ContactFinderDirectImport) -> ImportResult:
    """Import contacts from contact-finder skill (alternate format with 'contacts' array)."""
    result = ImportResult(
        success=True,
        skill_type="contact-finder"
    )

    for contact_entry in data.contacts:
        try:
            # Find existing prospect by institution name
            prospect = db.query(Prospect).filter(
                Prospect.name == contact_entry.institution,
                Prospect.deleted_at.is_(None)
            ).first()

            if not prospect:
                # Try fuzzy match on name
                prospect = db.query(Prospect).filter(
                    Prospect.name.ilike(f"%{contact_entry.institution}%"),
                    Prospect.deleted_at.is_(None)
                ).first()

            if not prospect:
                # Create a new prospect from the contact data
                # Determine venue type from institution name
                inst_lower = contact_entry.institution.lower()
                if "school district" in inst_lower or "high school" in inst_lower:
                    venue_type = "high_school_5a"  # Default for unknown classification
                elif "university" in inst_lower or "college" in inst_lower:
                    venue_type = "college_d2"
                else:
                    venue_type = "high_school_other"

                # Try to extract state from institution name or default
                state = "OH"  # Default, will be updated if we can determine it

                prospect = Prospect(
                    name=contact_entry.institution,
                    venue_type=venue_type,
                    state=state,
                    tier=map_tier(contact_entry.tier),
                    icp_score=contact_entry.score,
                    status=calculate_status_from_tier(map_tier(contact_entry.tier), False),
                    source="skill_import",
                    source_date=datetime.utcnow().date(),
                    research_notes=f"Outreach Recommendation: {contact_entry.outreach_recommendation}" if contact_entry.outreach_recommendation else None,
                )
                db.add(prospect)
                db.flush()
                result.prospects_created += 1
            else:
                # Update tier/score if provided and better
                if contact_entry.tier:
                    prospect.tier = map_tier(contact_entry.tier)
                if contact_entry.score and (not prospect.icp_score or contact_entry.score > prospect.icp_score):
                    prospect.icp_score = contact_entry.score

                # Append outreach recommendation to research notes
                if contact_entry.outreach_recommendation:
                    if prospect.research_notes:
                        prospect.research_notes += f"\n\nOutreach Recommendation: {contact_entry.outreach_recommendation}"
                    else:
                        prospect.research_notes = f"Outreach Recommendation: {contact_entry.outreach_recommendation}"

                result.prospects_updated += 1

            result.imported_ids.append(prospect.id)

            # Import primary contact
            if contact_entry.primary_contact:
                pc = contact_entry.primary_contact

                # Check for existing contact by email
                existing_contact = None
                if pc.email and pc.email.lower() not in ["unknown", "not found", ""]:
                    existing_contact = db.query(Contact).filter(
                        Contact.prospect_id == prospect.id,
                        Contact.email == pc.email,
                        Contact.deleted_at.is_(None)
                    ).first()

                # Get best phone number
                phone = pc.phone_direct or pc.phone or pc.phone_main

                contact_dict = {
                    "name": pc.name,
                    "title": pc.title,
                    "role": "decision_maker",  # Primary contact is usually decision maker
                    "email": pc.email if pc.email and pc.email.lower() not in ["unknown", "not found", ""] else None,
                    "phone": phone,
                    "linkedin_url": pc.linkedin_url if pc.linkedin_url and pc.linkedin_url.lower() not in ["not found", "unknown", ""] else None,
                    "is_primary": True,
                    "notes": pc.notes,
                }

                if existing_contact:
                    for key, value in contact_dict.items():
                        if value is not None:
                            setattr(existing_contact, key, value)
                    existing_contact.updated_at = datetime.utcnow()
                    result.contacts_updated += 1
                else:
                    contact = Contact(
                        prospect_id=prospect.id,
                        **contact_dict
                    )
                    db.add(contact)
                    result.contacts_created += 1

            # Import secondary contacts
            if contact_entry.secondary_contacts:
                for sc in contact_entry.secondary_contacts:
                    # Skip contacts without valid email
                    email = sc.email if sc.email and sc.email.lower() not in ["unknown", "not found", ""] else None

                    # Check for existing contact by email or by name+title
                    existing_contact = None
                    if email:
                        existing_contact = db.query(Contact).filter(
                            Contact.prospect_id == prospect.id,
                            Contact.email == email,
                            Contact.deleted_at.is_(None)
                        ).first()

                    contact_dict = {
                        "name": sc.name,
                        "title": sc.title,
                        "role": map_contact_role(None, sc.role_in_decision),
                        "email": email,
                        "phone": sc.phone if sc.phone and sc.phone.lower() not in ["unknown", "not found", ""] else None,
                        "linkedin_url": sc.linkedin_url if sc.linkedin_url and sc.linkedin_url.lower() not in ["not found", "unknown", ""] else None,
                        "is_primary": False,
                        "notes": sc.role_in_decision,
                    }

                    if existing_contact:
                        for key, value in contact_dict.items():
                            if value is not None:
                                setattr(existing_contact, key, value)
                        existing_contact.updated_at = datetime.utcnow()
                        result.contacts_updated += 1
                    else:
                        contact = Contact(
                            prospect_id=prospect.id,
                            **contact_dict
                        )
                        db.add(contact)
                        result.contacts_created += 1

            # Create activity for enrichment
            activity = Activity(
                prospect_id=prospect.id,
                type="note",
                description=f"Contacts enriched from contact-finder skill",
                agent_id="import_service",
            )
            db.add(activity)

        except Exception as e:
            result.errors.append(f"Error processing {contact_entry.institution}: {str(e)}")
            result.success = False

    db.commit()
    return result


def import_json_file(db: Session, json_data: dict) -> ImportResult:
    """Import JSON data, auto-detecting the skill type."""
    skill_type = detect_skill_type(json_data)

    if skill_type == "athletic-director-prospecting":
        parsed = AthleticDirectorImport(**json_data)
        return import_athletic_director_prospects(db, parsed)
    elif skill_type == "contact-finder-enrichment":
        parsed = ContactFinderImport(**json_data)
        return import_contact_finder_enrichment(db, parsed)
    elif skill_type == "contact-finder":
        parsed = ContactFinderDirectImport(**json_data)
        return import_contact_finder_direct(db, parsed)
    else:
        return ImportResult(
            success=False,
            skill_type="unknown",
            errors=[f"Unknown skill type: {skill_type}"]
        )
