"""Service for importing JSON data from Claude skills into the pipeline."""
import json
import time
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database.models import (
    Prospect, Contact, ProspectScore, Activity, AgentAuditLog,
    VENUE_TYPES, STATES, TIERS
)
from api.import_schemas import (
    AthleticDirectorImport, ContactFinderImport, ImportResult,
    ProspectDiscoveryData, EnrichedProspect, EnrichedContact,
    ContactFinderDirectImport, ContactFinderProspect,
    ContactFinderProspectsImport, ContactFinderProspectVariant,
    ContactFinderFlatImport, ContactFinderFlatProspect
)


def _retry_on_connection_error(db: Session, func, max_retries: int = 3):
    """Retry a database operation on connection errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            error_msg = str(e).lower()
            if "ssl" in error_msg or "connection" in error_msg or "closed" in error_msg:
                if attempt < max_retries - 1:
                    db.rollback()
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
            raise
    return func()  # Final attempt


def detect_skill_type(data: dict) -> str:
    """Detect the skill type from JSON data."""
    skill_type = data.get("skill_type", "")

    # Check explicit skill_type first
    if skill_type == "athletic-director-prospecting":
        return "athletic-director-prospecting"
    elif skill_type == "contact-finder-enrichment":
        return "contact-finder-enrichment"
    elif skill_type == "contact-finder":
        # contact-finder has three variants:
        # 1. 'contacts' array at root level
        # 2. 'prospects' array with nested contacts object (primary_decision_maker)
        # 3. 'prospects' array with flat contacts list
        if "prospects" in data and isinstance(data.get("prospects"), list):
            prospects = data.get("prospects", [])
            if prospects:
                first_prospect = prospects[0]
                contacts = first_prospect.get("contacts")
                if isinstance(contacts, dict):
                    # Nested structure with primary_decision_maker
                    return "contact-finder-prospects"
                elif isinstance(contacts, list):
                    # Flat contacts list
                    return "contact-finder-flat"
            return "contact-finder-prospects"
        elif "contacts" in data and isinstance(data.get("contacts"), list):
            return "contact-finder"  # variant with contacts array
        return "contact-finder"

    # Fallback detection based on structure
    if "prospects" in data:
        prospects = data.get("prospects", [])
        if prospects:
            first_prospect = prospects[0]
            # Check if it has institution data (athletic-director format)
            if "institution" in first_prospect and isinstance(first_prospect.get("institution"), dict):
                return "athletic-director-prospecting"
            # Check contacts structure
            contacts = first_prospect.get("contacts")
            if isinstance(contacts, dict):
                return "contact-finder-prospects"
            elif isinstance(contacts, list):
                return "contact-finder-flat"
        return "athletic-director-prospecting"
    elif "enriched_prospects" in data:
        return "contact-finder-enrichment"
    elif "contacts" in data and isinstance(data.get("contacts"), list):
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

            # Extract city/state from either format
            city = prospect_data.institution.city
            state = prospect_data.institution.state
            if prospect_data.institution.location:
                city = city or prospect_data.institution.location.city
                state = state or prospect_data.institution.location.state

            # Extract tier from either format
            tier_str = None
            if prospect_data.scoring and prospect_data.scoring.tier:
                tier_str = prospect_data.scoring.tier
            elif prospect_data.tier:
                tier_str = prospect_data.tier

            # Extract score from either format
            icp_score = None
            if prospect_data.scoring and prospect_data.scoring.icp_score:
                icp_score = prospect_data.scoring.icp_score
            elif prospect_data.scoring_breakdown and prospect_data.scoring_breakdown.total_score:
                icp_score = prospect_data.scoring_breakdown.total_score
            elif prospect_data.score:
                icp_score = prospect_data.score

            # Extract facility data from either format
            stadium_name = None
            current_lighting = None
            lighting_age = None
            if prospect_data.facility:
                stadium_name = prospect_data.facility.primary_venue
                current_lighting = prospect_data.facility.current_lighting
                lighting_age = prospect_data.facility.lighting_age_years
            elif prospect_data.facility_assessment:
                stadium_name = prospect_data.facility_assessment.stadium_name
                current_lighting = prospect_data.facility_assessment.current_lighting

            # Extract constraint hypothesis from either format
            constraint_hypothesis = None
            if prospect_data.facility_hypothesis and prospect_data.facility_hypothesis.statement:
                constraint_hypothesis = prospect_data.facility_hypothesis.statement
            elif prospect_data.facility_assessment and prospect_data.facility_assessment.facility_hypothesis:
                constraint_hypothesis = prospect_data.facility_assessment.facility_hypothesis

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
            # Add key signals from facility_assessment
            if prospect_data.facility_assessment and prospect_data.facility_assessment.key_signals:
                research_notes_parts.append("Key Signals:\n- " + "\n- ".join(prospect_data.facility_assessment.key_signals))
            # Add discovery questions
            if prospect_data.discovery_questions:
                research_notes_parts.append("Discovery Questions:\n- " + "\n- ".join(prospect_data.discovery_questions))

            research_notes = "\n\n".join(research_notes_parts) if research_notes_parts else None

            # Determine if we have research
            has_research = bool(constraint_hypothesis)

            tier = map_tier(tier_str)

            prospect_dict = {
                "name": prospect_data.institution.name,
                "venue_type": map_institution_type_to_venue_type(prospect_data.institution.type),
                "state": map_state(state),
                "city": city,
                "conference": prospect_data.institution.conference,
                "enrollment": prospect_data.institution.enrollment,
                "stadium_name": stadium_name,
                "current_lighting_type": map_lighting_type(current_lighting),
                "current_lighting_age_years": lighting_age if isinstance(lighting_age, int) else None,
                "broadcast_requirements": map_broadcast_requirements(
                    prospect_data.facility.broadcast_capable if prospect_data.facility else None
                ),
                "tier": tier,
                "icp_score": icp_score,
                "constraint_hypothesis": constraint_hypothesis,
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

            # Get primary decision maker from either format
            dm = None
            if prospect_data.decision_maker and prospect_data.decision_maker.name:
                dm = prospect_data.decision_maker
            elif prospect_data.decision_makers and prospect_data.decision_makers.primary:
                dm = prospect_data.decision_makers.primary

            # Import primary decision maker as contact
            if dm and dm.name:
                email = dm.email if dm.email and dm.email.lower() not in ["unknown", "not found", ""] else None
                existing_contact = db.query(Contact).filter(
                    Contact.prospect_id == prospect.id,
                    Contact.email == email,
                    Contact.deleted_at.is_(None)
                ).first() if email else None

                if not existing_contact:
                    linkedin = dm.linkedin_url if dm.linkedin_url and dm.linkedin_url.lower() not in ["not found", "unknown", ""] else None
                    contact = Contact(
                        prospect_id=prospect.id,
                        name=dm.name,
                        title=dm.title,
                        role=map_contact_role(dm.authority_level, None),
                        email=email,
                        phone=dm.phone,
                        linkedin_url=linkedin,
                        is_primary=True,
                        notes=dm.notes,
                    )
                    db.add(contact)
                    result.contacts_created += 1

            # Get secondary contacts from either format
            secondary_contacts = prospect_data.secondary_contacts or []
            if prospect_data.decision_makers and prospect_data.decision_makers.secondary:
                secondary_contacts = prospect_data.decision_makers.secondary

            # Import secondary contacts
            for sc in secondary_contacts:
                if not sc.name or sc.name.lower() == "unknown":
                    continue
                email = sc.email if sc.email and sc.email.lower() not in ["unknown", "not found", ""] else None
                # Skip if email matches pattern placeholder
                if email and "email pattern" in email.lower():
                    email = None

                existing_contact = db.query(Contact).filter(
                    Contact.prospect_id == prospect.id,
                    Contact.email == email,
                    Contact.deleted_at.is_(None)
                ).first() if email else None

                if not existing_contact:
                    linkedin = sc.linkedin_url if sc.linkedin_url and sc.linkedin_url.lower() not in ["not found", "unknown", ""] else None
                    notes = sc.role_in_decision or sc.notes if hasattr(sc, 'notes') else sc.role_in_decision
                    contact = Contact(
                        prospect_id=prospect.id,
                        name=sc.name,
                        title=sc.title,
                        role=map_contact_role(getattr(sc, 'authority_level', None) if hasattr(sc, 'authority_level') else None, sc.role_in_decision),
                        email=email,
                        phone=sc.phone,
                        linkedin_url=linkedin,
                        is_primary=False,
                        notes=notes,
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
            db.rollback()
            result.errors.append(f"Error importing {prospect_data.institution.name}: {str(e)}")
            result.success = False
            return result  # Return early on error after rollback

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
            db.rollback()
            result.errors.append(f"Error enriching {enriched.institution}: {str(e)}")
            result.success = False
            return result  # Return early on error after rollback

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
            db.rollback()
            result.errors.append(f"Error processing {contact_entry.institution}: {str(e)}")
            result.success = False
            return result  # Return early on error after rollback

    db.commit()
    return result


def import_contact_finder_prospects(db: Session, data: ContactFinderProspectsImport) -> ImportResult:
    """Import contact-finder data with 'prospects' array variant.

    This variant has a nested contacts structure within each prospect:
    - contacts.primary_decision_maker
    - contacts.secondary_contacts[]
    - contacts.general_contact
    - outreach_recommendations object
    """
    result = ImportResult(
        success=True,
        skill_type="contact-finder-prospects",
    )

    for prospect_entry in data.prospects:
        try:
            # Find or create prospect by institution name
            prospect = db.query(Prospect).filter(
                Prospect.name == prospect_entry.institution,
                Prospect.deleted_at.is_(None)
            ).first()

            if not prospect:
                # Create new prospect
                # Determine venue type from institution name
                inst_lower = prospect_entry.institution.lower()
                if "school district" in inst_lower or "high school" in inst_lower or "schools" in inst_lower:
                    venue_type = "high_school_5a"
                elif "university" in inst_lower or "college" in inst_lower:
                    venue_type = "college_d2"
                else:
                    venue_type = "high_school_other"

                # Extract state from location if provided
                state = "OH"  # Default
                if prospect_entry.location:
                    # Try to extract state from "City, ST" format
                    parts = prospect_entry.location.split(",")
                    if len(parts) >= 2:
                        state_part = parts[-1].strip().upper()
                        if state_part in STATES:
                            state = state_part

                # Build research notes from outreach recommendations
                research_notes = None
                if prospect_entry.outreach_recommendations:
                    rec = prospect_entry.outreach_recommendations
                    notes_parts = []
                    if rec.approach:
                        notes_parts.append(f"Approach: {rec.approach}")
                    if rec.timing:
                        notes_parts.append(f"Timing: {rec.timing}")
                    if rec.talking_points:
                        notes_parts.append("Talking Points:")
                        for tp in rec.talking_points:
                            notes_parts.append(f"  - {tp}")
                    if rec.email_subject_suggestion:
                        notes_parts.append(f"Suggested Subject: {rec.email_subject_suggestion}")
                    research_notes = "\n".join(notes_parts)

                prospect = Prospect(
                    name=prospect_entry.institution,
                    venue_type=venue_type,
                    state=state,
                    tier=map_tier(prospect_entry.tier),
                    icp_score=prospect_entry.score,
                    status=calculate_status_from_tier(map_tier(prospect_entry.tier), False),
                    source="skill_import",
                    source_date=datetime.utcnow().date(),
                    research_notes=research_notes,
                )
                db.add(prospect)
                db.flush()
                result.prospects_created += 1
            else:
                # Update tier/score if provided and better
                if prospect_entry.tier:
                    prospect.tier = map_tier(prospect_entry.tier)
                if prospect_entry.score and (not prospect.icp_score or prospect_entry.score > prospect.icp_score):
                    prospect.icp_score = prospect_entry.score

                # Append outreach recommendations to research notes
                if prospect_entry.outreach_recommendations:
                    rec = prospect_entry.outreach_recommendations
                    notes_parts = []
                    if rec.approach:
                        notes_parts.append(f"Approach: {rec.approach}")
                    if rec.timing:
                        notes_parts.append(f"Timing: {rec.timing}")
                    if rec.talking_points:
                        notes_parts.append("Talking Points:")
                        for tp in rec.talking_points:
                            notes_parts.append(f"  - {tp}")
                    if rec.email_subject_suggestion:
                        notes_parts.append(f"Suggested Subject: {rec.email_subject_suggestion}")

                    new_notes = "\n".join(notes_parts)
                    if prospect.research_notes:
                        prospect.research_notes += f"\n\n{new_notes}"
                    else:
                        prospect.research_notes = new_notes

                result.prospects_updated += 1

            result.imported_ids.append(prospect.id)

            # Import contacts from nested structure
            if prospect_entry.contacts:
                contacts_obj = prospect_entry.contacts

                # Import primary decision maker
                if contacts_obj.primary_decision_maker:
                    pdm = contacts_obj.primary_decision_maker

                    # Check for existing contact by email
                    existing_contact = None
                    email = pdm.email if pdm.email and pdm.email.lower() not in ["unknown", "not found", ""] else None
                    if email:
                        existing_contact = db.query(Contact).filter(
                            Contact.prospect_id == prospect.id,
                            Contact.email == email,
                            Contact.deleted_at.is_(None)
                        ).first()

                    # Build notes from various fields
                    notes_parts = []
                    if pdm.notes:
                        notes_parts.append(pdm.notes)
                    if pdm.authority_level:
                        notes_parts.append(f"Authority: {pdm.authority_level}")
                    if pdm.project_involvement:
                        notes_parts.append(f"Project involvement: {pdm.project_involvement}")
                    notes = " | ".join(notes_parts) if notes_parts else None

                    contact_dict = {
                        "name": pdm.name,
                        "title": pdm.title,
                        "role": "decision_maker",
                        "email": email,
                        "phone": pdm.phone if pdm.phone and pdm.phone.lower() not in ["unknown", "not found", ""] else None,
                        "linkedin_url": pdm.linkedin_url if pdm.linkedin_url and str(pdm.linkedin_url).lower() not in ["not found", "unknown", "", "none"] else None,
                        "is_primary": True,
                        "notes": notes,
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
                if contacts_obj.secondary_contacts:
                    for sc in contacts_obj.secondary_contacts:
                        email = sc.email if sc.email and sc.email.lower() not in ["unknown", "not found", ""] else None

                        # Check for existing contact by email
                        existing_contact = None
                        if email:
                            existing_contact = db.query(Contact).filter(
                                Contact.prospect_id == prospect.id,
                                Contact.email == email,
                                Contact.deleted_at.is_(None)
                            ).first()

                        # Map authority level to role (valid: decision_maker, influencer, champion, blocker, unknown)
                        role = "unknown"
                        if sc.authority_level:
                            auth_lower = sc.authority_level.lower()
                            if "executive" in auth_lower or "superintendent" in auth_lower:
                                role = "decision_maker"
                            elif "board" in auth_lower:
                                role = "influencer"
                            elif "financial" in auth_lower:
                                role = "influencer"
                            elif "admin" in auth_lower:
                                role = "blocker"  # Administrative gatekeepers
                            elif "support" in auth_lower:
                                role = "unknown"

                        # Build notes from various fields
                        notes_parts = []
                        if sc.notes:
                            notes_parts.append(sc.notes)
                        if sc.authority_level:
                            notes_parts.append(f"Authority: {sc.authority_level}")
                        if sc.project_involvement:
                            notes_parts.append(f"Project: {sc.project_involvement}")
                        notes = " | ".join(notes_parts) if notes_parts else None

                        contact_dict = {
                            "name": sc.name,
                            "title": sc.title,
                            "role": role,
                            "email": email,
                            "phone": sc.phone if sc.phone and sc.phone.lower() not in ["unknown", "not found", ""] else None,
                            "linkedin_url": sc.linkedin_url if sc.linkedin_url and str(sc.linkedin_url).lower() not in ["not found", "unknown", "", "none"] else None,
                            "is_primary": False,
                            "notes": notes,
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
                description=f"Contacts enriched from contact-finder skill (prospects variant)",
                agent_id="import_service",
            )
            db.add(activity)

        except Exception as e:
            db.rollback()
            result.errors.append(f"Error processing {prospect_entry.institution}: {str(e)}")
            result.success = False
            return result  # Return early on error after rollback

    db.commit()
    return result


def import_contact_finder_flat(db: Session, data: ContactFinderFlatImport) -> ImportResult:
    """Import contact-finder data with flat contacts list variant.

    This variant has a simple contacts array within each prospect:
    - prospects[].contacts[] - flat list of all contacts
    - prospects[].recommended_outreach_order - list of names in order
    """
    result = ImportResult(
        success=True,
        skill_type="contact-finder-flat",
    )

    for prospect_entry in data.prospects:
        try:
            # Find or create prospect by institution name
            prospect = db.query(Prospect).filter(
                Prospect.name == prospect_entry.institution,
                Prospect.deleted_at.is_(None)
            ).first()

            if not prospect:
                # Create new prospect
                inst_lower = prospect_entry.institution.lower()
                if "school district" in inst_lower or "high school" in inst_lower or "schools" in inst_lower:
                    venue_type = "high_school_5a"
                elif "university" in inst_lower or "college" in inst_lower:
                    venue_type = "college_d2"
                else:
                    venue_type = "high_school_other"

                state = map_state(prospect_entry.state)

                prospect = Prospect(
                    name=prospect_entry.institution,
                    venue_type=venue_type,
                    city=prospect_entry.city,
                    state=state,
                    tier=map_tier(prospect_entry.tier),
                    icp_score=prospect_entry.score,
                    status=calculate_status_from_tier(map_tier(prospect_entry.tier), False),
                    source="skill_import",
                    source_date=datetime.utcnow().date(),
                )
                db.add(prospect)
                db.flush()
                result.prospects_created += 1
            else:
                # Update tier/score if provided and better
                if prospect_entry.tier:
                    prospect.tier = map_tier(prospect_entry.tier)
                if prospect_entry.score and (not prospect.icp_score or prospect_entry.score > prospect.icp_score):
                    prospect.icp_score = prospect_entry.score
                if prospect_entry.city and not prospect.city:
                    prospect.city = prospect_entry.city
                if prospect_entry.state:
                    prospect.state = map_state(prospect_entry.state)

                result.prospects_updated += 1

            result.imported_ids.append(prospect.id)

            # Determine primary contact from recommended_outreach_order
            primary_contact_name = None
            if prospect_entry.recommended_outreach_order and len(prospect_entry.recommended_outreach_order) > 0:
                # Extract name from first entry (format: "Name (title)")
                first_entry = prospect_entry.recommended_outreach_order[0]
                if "(" in first_entry:
                    primary_contact_name = first_entry.split("(")[0].strip()
                else:
                    primary_contact_name = first_entry.strip()

            # Import contacts
            for contact_data in prospect_entry.contacts:
                # Skip low-confidence or unknown contacts
                if contact_data.confidence and contact_data.confidence < 60:
                    continue
                if contact_data.name.lower() == "unknown":
                    continue

                email = contact_data.email if contact_data.email and contact_data.email.lower() not in ["unknown", "not found", ""] else None

                # Check for existing contact by email
                existing_contact = None
                if email:
                    existing_contact = db.query(Contact).filter(
                        Contact.prospect_id == prospect.id,
                        Contact.email == email,
                        Contact.deleted_at.is_(None)
                    ).first()

                # Determine if this is the primary contact
                is_primary = False
                if primary_contact_name and contact_data.name:
                    is_primary = primary_contact_name.lower() in contact_data.name.lower()

                # Map authority level and seniority to role
                role = "unknown"
                if contact_data.authority_level:
                    auth_lower = contact_data.authority_level.lower()
                    if auth_lower == "high":
                        role = "decision_maker"
                    elif auth_lower == "medium":
                        role = "influencer"
                    elif auth_lower == "low":
                        role = "influencer"
                elif contact_data.seniority:
                    sen_lower = contact_data.seniority.lower()
                    if sen_lower in ["executive", "director"]:
                        role = "decision_maker"
                    elif sen_lower in ["manager", "senior"]:
                        role = "influencer"

                contact_dict = {
                    "name": contact_data.name,
                    "title": contact_data.title,
                    "role": role,
                    "email": email,
                    "phone": contact_data.phone if contact_data.phone and contact_data.phone.lower() not in ["unknown", "not found", ""] else None,
                    "linkedin_url": contact_data.linkedin_url if contact_data.linkedin_url and contact_data.linkedin_url.lower() not in ["not found", "unknown", ""] else None,
                    "is_primary": is_primary,
                    "notes": contact_data.notes,
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
                description=f"Contacts enriched from contact-finder skill ({len(prospect_entry.contacts)} contacts)",
                agent_id="import_service",
            )
            db.add(activity)

        except Exception as e:
            db.rollback()
            result.errors.append(f"Error processing {prospect_entry.institution}: {str(e)}")
            result.success = False
            return result  # Return early on error after rollback

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
    elif skill_type == "contact-finder-prospects":
        parsed = ContactFinderProspectsImport(**json_data)
        return import_contact_finder_prospects(db, parsed)
    elif skill_type == "contact-finder-flat":
        parsed = ContactFinderFlatImport(**json_data)
        return import_contact_finder_flat(db, parsed)
    else:
        return ImportResult(
            success=False,
            skill_type="unknown",
            errors=[f"Unknown skill type: {skill_type}"]
        )
