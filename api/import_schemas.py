"""Pydantic schemas for JSON import from Claude skills."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ============================================================================
# Athletic Director Prospecting Skill Schema
# ============================================================================

class InstitutionData(BaseModel):
    name: str
    type: str  # "High School", "Division II College", etc.
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    enrollment: Optional[int] = None
    enrollment_range: Optional[str] = None
    conference: Optional[str] = None
    athletics_website: Optional[str] = None


class FacilityData(BaseModel):
    primary_venue: Optional[str] = None
    current_lighting: Optional[str] = None
    lighting_age_years: Optional[int] = None
    estimated_condition: Optional[str] = None
    broadcast_capable: Optional[bool] = None
    multi_sport_facility: Optional[bool] = None
    estimated_project_size: Optional[str] = None
    facility_notes: Optional[str] = None


class ScoreBreakdownItem(BaseModel):
    score: int
    weight: int
    weighted: int


class ScoringData(BaseModel):
    facility_condition_score: Optional[int] = None
    institution_size_score: Optional[int] = None
    budget_signals_score: Optional[int] = None
    decision_maker_access_score: Optional[int] = None
    timing_triggers_score: Optional[int] = None
    geographic_fit_score: Optional[int] = None
    competitive_pressure_score: Optional[int] = None
    purchase_readiness_score: Optional[int] = None
    icp_score: Optional[int] = None
    readiness_score: Optional[int] = None
    total_score: Optional[int] = None
    tier: Optional[str] = None
    score_breakdown: Optional[dict] = None


class FacilityHypothesis(BaseModel):
    statement: Optional[str] = None
    target_facility: Optional[str] = None
    solution_type: Optional[str] = None
    primary_driver: Optional[str] = None
    estimated_value: Optional[str] = None


class DecisionMakerData(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    authority_level: Optional[str] = None
    tenure_years: Optional[int] = None
    notes: Optional[str] = None


class SecondaryContactData(BaseModel):
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_in_decision: Optional[str] = None


class SalesReadinessData(BaseModel):
    opportunity_summary: Optional[str] = None
    key_assumptions: Optional[List[str]] = None
    required_validation: Optional[List[str]] = None
    discovery_questions: Optional[List[str]] = None


class OutreachData(BaseModel):
    timing_triggers: Optional[List[str]] = None
    personalization_hooks: Optional[List[str]] = None
    recommended_approach: Optional[str] = None


class NextActionData(BaseModel):
    action: Optional[str] = None
    priority: Optional[str] = None
    target_date: Optional[str] = None
    notes: Optional[str] = None


class ProspectDiscoveryData(BaseModel):
    """Full prospect data from athletic-director-prospecting skill."""
    institution: InstitutionData
    facility: Optional[FacilityData] = None
    scoring: Optional[ScoringData] = None
    deal_risk_flags: Optional[List[str]] = None
    facility_hypothesis: Optional[FacilityHypothesis] = None
    decision_maker: Optional[DecisionMakerData] = None
    secondary_contacts: Optional[List[SecondaryContactData]] = None
    sales_readiness: Optional[SalesReadinessData] = None
    outreach: Optional[OutreachData] = None
    next_action: Optional[NextActionData] = None


class AthleticDirectorImport(BaseModel):
    """Root schema for athletic-director-prospecting skill output."""
    skill_type: str = "athletic-director-prospecting"
    version: Optional[str] = None
    generated_at: Optional[str] = None
    prospect_count: Optional[int] = None
    prospects: List[ProspectDiscoveryData]


# ============================================================================
# Contact Finder Enrichment Skill Schema
# ============================================================================

class EnrichedContact(BaseModel):
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence: Optional[int] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    source: Optional[str] = None
    authority_level: Optional[str] = None
    role_in_decision: Optional[str] = None
    tenure_years: Optional[int] = None
    tenure_at_uf: Optional[int] = None  # University of Findlay specific
    ad_since: Optional[str] = None
    vp_since: Optional[str] = None
    notes: Optional[str] = None
    cell: Optional[str] = None


class OutreachSequenceItem(BaseModel):
    order: int
    contact: str
    reason: Optional[str] = None


class EnrichedProspect(BaseModel):
    """Enriched prospect data from contact-finder skill."""
    institution: str
    tier: Optional[str] = None
    total_score: Optional[int] = None
    contacts: List[EnrichedContact]
    recommended_outreach_sequence: Optional[List[OutreachSequenceItem]] = None


class ContactFinderImport(BaseModel):
    """Root schema for contact-finder-enrichment skill output."""
    skill_type: str = "contact-finder-enrichment"
    source_file: Optional[str] = None
    enriched_at: Optional[str] = None
    notes: Optional[str] = None
    prospect_count: Optional[int] = None
    enriched_prospects: List[EnrichedProspect]
    search_metadata: Optional[dict] = None


# ============================================================================
# Contact Finder Skill Schema (alternate format)
# ============================================================================

class ContactFinderPrimaryContact(BaseModel):
    """Primary contact from contact-finder skill."""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_direct: Optional[str] = None
    phone_main: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter: Optional[str] = None
    confidence: Optional[int] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class ContactFinderSecondaryContact(BaseModel):
    """Secondary contact from contact-finder skill."""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role_in_decision: Optional[str] = None


class ContactFinderProspect(BaseModel):
    """Prospect entry from contact-finder skill."""
    prospect_number: Optional[int] = None
    institution: str
    tier: Optional[str] = None
    score: Optional[int] = None
    primary_contact: Optional[ContactFinderPrimaryContact] = None
    secondary_contacts: Optional[List[ContactFinderSecondaryContact]] = None
    outreach_recommendation: Optional[str] = None


class ContactFinderDirectImport(BaseModel):
    """Root schema for contact-finder skill output (alternate format with 'contacts' array)."""
    skill_type: str = "contact-finder"
    version: Optional[str] = None
    generated_at: Optional[str] = None
    note: Optional[str] = None
    prospect_count: Optional[int] = None
    contacts: List[ContactFinderProspect]
    summary: Optional[dict] = None


# ============================================================================
# Contact Finder Skill Schema (variant with 'prospects' array and nested contacts)
# ============================================================================

class ContactFinderDecisionMaker(BaseModel):
    """Primary decision maker from contact-finder prospects variant."""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence: Optional[int] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    authority_level: Optional[str] = None
    project_involvement: Optional[str] = None


class ContactFinderNestedSecondary(BaseModel):
    """Secondary contact from contact-finder prospects variant."""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence: Optional[int] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    authority_level: Optional[str] = None
    project_involvement: Optional[str] = None


class ContactFinderGeneralContact(BaseModel):
    """General contact info from contact-finder prospects variant."""
    phone: Optional[str] = None
    fax: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None


class ContactFinderContactsObject(BaseModel):
    """Nested contacts object from contact-finder prospects variant."""
    primary_decision_maker: Optional[ContactFinderDecisionMaker] = None
    secondary_contacts: Optional[List[ContactFinderNestedSecondary]] = None
    general_contact: Optional[ContactFinderGeneralContact] = None


class ContactFinderOutreachRecs(BaseModel):
    """Outreach recommendations from contact-finder prospects variant."""
    approach: Optional[str] = None
    timing: Optional[str] = None
    talking_points: Optional[List[str]] = None
    email_subject_suggestion: Optional[str] = None


class ContactFinderProspectVariant(BaseModel):
    """Prospect entry from contact-finder skill (prospects variant)."""
    prospect_id: Optional[int] = None
    institution: str
    location: Optional[str] = None
    tier: Optional[str] = None
    score: Optional[int] = None
    contacts: Optional[ContactFinderContactsObject] = None
    outreach_recommendations: Optional[ContactFinderOutreachRecs] = None


class ContactFinderProspectsImport(BaseModel):
    """Root schema for contact-finder skill output (variant with 'prospects' array)."""
    skill_type: str = "contact-finder"
    enrichment_date: Optional[str] = None
    data_source: Optional[str] = None
    prospect_count: Optional[int] = None
    prospects: List[ContactFinderProspectVariant]
    summary: Optional[dict] = None


# ============================================================================
# Generic Import Wrapper
# ============================================================================

class ImportResult(BaseModel):
    """Result of an import operation."""
    success: bool
    skill_type: str
    prospects_created: int = 0
    prospects_updated: int = 0
    contacts_created: int = 0
    contacts_updated: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    imported_ids: List[str] = []
