"""Pydantic schemas for API request/response validation."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


# Base response wrapper
class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None


# Prospect schemas
class ProspectBase(BaseModel):
    name: str
    venue_type: str
    state: str
    city: Optional[str] = None
    address: Optional[str] = None
    classification: Optional[str] = None
    conference: Optional[str] = None
    enrollment: Optional[int] = None
    primary_sport: Optional[str] = None
    stadium_name: Optional[str] = None
    seating_capacity: Optional[int] = None
    current_lighting_type: Optional[str] = None
    current_lighting_age_years: Optional[int] = None
    has_night_games: bool = True
    broadcast_requirements: Optional[str] = None
    estimated_project_timeline: Optional[str] = None
    budget_cycle_month: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class ProspectCreate(ProspectBase):
    pass


class ProspectUpdate(BaseModel):
    name: Optional[str] = None
    venue_type: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    classification: Optional[str] = None
    conference: Optional[str] = None
    enrollment: Optional[int] = None
    primary_sport: Optional[str] = None
    stadium_name: Optional[str] = None
    seating_capacity: Optional[int] = None
    current_lighting_type: Optional[str] = None
    current_lighting_age_years: Optional[int] = None
    has_night_games: Optional[bool] = None
    broadcast_requirements: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[str] = None
    icp_score: Optional[int] = None
    constraint_hypothesis: Optional[str] = None
    value_proposition: Optional[str] = None
    research_notes: Optional[str] = None
    estimated_project_timeline: Optional[str] = None
    budget_cycle_month: Optional[int] = None


class ProspectRead(ProspectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    tier: Optional[str] = None
    icp_score: Optional[int] = None
    constraint_hypothesis: Optional[str] = None
    value_proposition: Optional[str] = None
    research_notes: Optional[str] = None
    source_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class ProspectDetail(ProspectRead):
    """Extended prospect with related data."""
    contacts: List["ContactRead"] = []
    scores: List["ProspectScoreRead"] = []
    recent_activities: List["ActivityRead"] = []


# Contact schemas
class ContactBase(BaseModel):
    name: str
    title: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    prospect_id: str


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prospect_id: str
    last_contacted_at: Optional[datetime] = None
    last_response_at: Optional[datetime] = None
    engagement_score: int = 0
    created_at: datetime
    updated_at: datetime


# Prospect Score schemas
class ProspectScoreBase(BaseModel):
    dimension: str
    score: int = Field(ge=1, le=10)
    weight: int = Field(ge=1, le=5)
    notes: Optional[str] = None


class ProspectScoreCreate(ProspectScoreBase):
    prospect_id: str
    scored_by: Optional[str] = None


class ProspectScoreRead(ProspectScoreBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prospect_id: str
    scored_at: datetime
    scored_by: Optional[str] = None


# Activity schemas
class ActivityBase(BaseModel):
    type: str
    direction: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None


class ActivityCreate(ActivityBase):
    prospect_id: str
    contact_id: Optional[str] = None
    email_template_id: Optional[str] = None
    email_sequence_step: Optional[int] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None


class ActivityRead(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prospect_id: str
    contact_id: Optional[str] = None
    email_template_id: Optional[str] = None
    email_sequence_step: Optional[int] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime


# Agent Run schemas
class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    error_message: Optional[str] = None
    trigger: Optional[str] = None


class AgentHealth(BaseModel):
    """Agent health status."""
    agent_name: str
    status: str  # healthy, degraded, down
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    runs_last_24h: int = 0
    errors_last_24h: int = 0


# Outreach schemas
class OutreachSequenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prospect_id: str
    contact_id: str
    template_id: str
    tier: str
    status: str
    current_step: int
    total_steps: int
    started_at: Optional[datetime] = None
    next_step_at: Optional[datetime] = None
    emails_sent: int
    emails_opened: int
    replies_received: int
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PendingApproval(BaseModel):
    """Pending A1 approval with full context."""
    sequence: OutreachSequenceRead
    prospect: ProspectRead
    contact: ContactRead
    email_subject: str
    email_body: str


class OutreachTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tier: str
    step_number: int
    subject_template: str
    body_template: str
    days_after_previous: int
    is_active: bool


# Hygiene Flag schemas
class HygieneFlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prospect_id: str
    flag_type: str
    severity: str
    message: str
    suggested_action: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime


# Pipeline Stats
class PipelineStats(BaseModel):
    """Overview statistics for the pipeline."""
    total_prospects: int
    prospects_by_status: dict[str, int]
    prospects_by_tier: dict[str, int]
    emails_sent_today: int
    responses_today: int
    pending_approvals: int
    unresolved_flags: int


# Forward references
ProspectDetail.model_rebuild()
