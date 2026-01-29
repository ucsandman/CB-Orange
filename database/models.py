"""SQLAlchemy models for Sportsbeams Pipeline."""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, Date,
    Float, ForeignKey, CheckConstraint, Index, event
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def generate_uuid():
    """Generate a lowercase hex UUID."""
    return uuid.uuid4().hex


# Enums as string literals for SQLite compatibility
VENUE_TYPES = (
    'college_d1', 'college_d2', 'college_d3', 'college_naia',
    'high_school_6a', 'high_school_5a', 'high_school_4a',
    'high_school_3a', 'high_school_other'
)

STATES = ('OH', 'IN', 'PA', 'KY', 'IL', 'OTHER')

PROSPECT_STATUSES = (
    'identified', 'needs_scoring', 'scored', 'needs_research',
    'research_complete', 'ready_for_outreach', 'outreach_active',
    'engaged', 'nurture', 'deprioritized'
)

TIERS = ('A1', 'A2', 'B', 'C', 'D')

CONTACT_ROLES = ('decision_maker', 'influencer', 'champion', 'blocker', 'unknown')

SCORE_DIMENSIONS = (
    'venue_type', 'geography', 'budget_signals', 'current_lighting_age',
    'night_game_frequency', 'broadcast_requirements', 'decision_maker_access',
    'project_timeline'
)

ACTIVITY_TYPES = (
    'email_sent', 'email_received', 'email_opened', 'email_clicked',
    'call', 'meeting', 'note', 'status_change', 'score_change',
    'research_completed', 'outreach_started', 'outreach_paused', 'outreach_completed'
)

SEQUENCE_STATUSES = ('pending', 'active', 'paused', 'completed', 'stopped')

AGENT_NAMES = ('prospector', 'hygiene', 'researcher', 'outreach', 'orchestrator')

AGENT_RUN_STATUSES = ('running', 'completed', 'failed')

FLAG_TYPES = (
    'missing_contact', 'missing_email', 'stale_data', 'score_anomaly',
    'duplicate_suspect', 'data_quality', 'outreach_blocked'
)

FLAG_SEVERITIES = ('info', 'warning', 'critical')

BID_SOURCES = ('bidnet', 'onvia', 'public_purchase', 'manual')

BID_STATUSES = ('new', 'reviewed', 'matched', 'not_relevant')


class Prospect(Base):
    """Primary table for athletic venues (schools/colleges)."""
    __tablename__ = 'prospects'

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Basic Info
    name = Column(String(255), nullable=False)
    venue_type = Column(String(50), nullable=False)
    state = Column(String(10), nullable=False)
    city = Column(String(100))
    address = Column(Text)

    # Classification (for high schools)
    classification = Column(String(10))
    conference = Column(String(100))
    enrollment = Column(Integer)

    # Facility Info
    primary_sport = Column(String(50))
    stadium_name = Column(String(255))
    seating_capacity = Column(Integer)
    current_lighting_type = Column(String(50))
    current_lighting_age_years = Column(Integer)
    has_night_games = Column(Boolean, default=True)
    broadcast_requirements = Column(String(50))

    # Pipeline Status
    status = Column(String(50), nullable=False, default='identified')
    tier = Column(String(5))
    icp_score = Column(Integer)

    # Research
    constraint_hypothesis = Column(Text)
    value_proposition = Column(Text)
    research_notes = Column(Text)

    # Timing
    estimated_project_timeline = Column(String(50))
    budget_cycle_month = Column(Integer)

    # Source Tracking
    source = Column(String(50))
    source_url = Column(Text)
    source_date = Column(Date)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    contacts = relationship("Contact", back_populates="prospect", lazy="dynamic")
    scores = relationship("ProspectScore", back_populates="prospect", lazy="dynamic")
    activities = relationship("Activity", back_populates="prospect", lazy="dynamic")
    outreach_sequences = relationship("OutreachSequence", back_populates="prospect", lazy="dynamic")
    hygiene_flags = relationship("HygieneFlag", back_populates="prospect", lazy="dynamic")

    __table_args__ = (
        CheckConstraint(f"venue_type IN {VENUE_TYPES}"),
        CheckConstraint(f"state IN {STATES}"),
        CheckConstraint(f"status IN {PROSPECT_STATUSES}"),
        CheckConstraint(f"tier IN {TIERS} OR tier IS NULL"),
        Index('idx_prospects_status', 'status'),
        Index('idx_prospects_tier', 'tier'),
        Index('idx_prospects_state', 'state'),
        Index('idx_prospects_venue_type', 'venue_type'),
    )


class Contact(Base):
    """People associated with prospects."""
    __tablename__ = 'contacts'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    prospect_id = Column(String(32), ForeignKey('prospects.id'), nullable=False)

    # Basic Info
    name = Column(String(255), nullable=False)
    title = Column(String(100))
    role = Column(String(50))

    # Contact Info
    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(Text)

    # Engagement
    is_primary = Column(Boolean, default=False)
    last_contacted_at = Column(DateTime)
    last_response_at = Column(DateTime)
    engagement_score = Column(Integer, default=0)

    # Notes
    notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    prospect = relationship("Prospect", back_populates="contacts")
    activities = relationship("Activity", back_populates="contact", lazy="dynamic")
    outreach_sequences = relationship("OutreachSequence", back_populates="contact", lazy="dynamic")

    __table_args__ = (
        CheckConstraint(f"role IN {CONTACT_ROLES} OR role IS NULL"),
        Index('idx_contacts_prospect_id', 'prospect_id'),
        Index('idx_contacts_email', 'email'),
    )


class ProspectScore(Base):
    """Individual dimension scores for ICP calculation."""
    __tablename__ = 'prospect_scores'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    prospect_id = Column(String(32), ForeignKey('prospects.id'), nullable=False)

    # Score Details
    dimension = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    notes = Column(Text)

    # Metadata
    scored_at = Column(DateTime, default=datetime.utcnow)
    scored_by = Column(String(100))

    # Relationships
    prospect = relationship("Prospect", back_populates="scores")

    __table_args__ = (
        CheckConstraint(f"dimension IN {SCORE_DIMENSIONS}"),
        CheckConstraint("score BETWEEN 1 AND 10"),
        CheckConstraint("weight BETWEEN 1 AND 5"),
        Index('idx_prospect_scores_prospect_id', 'prospect_id'),
    )


class Activity(Base):
    """All interactions and events related to prospects."""
    __tablename__ = 'activities'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    prospect_id = Column(String(32), ForeignKey('prospects.id'), nullable=False)
    contact_id = Column(String(32), ForeignKey('contacts.id'))

    # Activity Details
    type = Column(String(50), nullable=False)
    direction = Column(String(20))
    subject = Column(String(255))
    description = Column(Text)

    # For emails
    email_template_id = Column(String(32))
    email_sequence_step = Column(Integer)

    # Attribution
    agent_id = Column(String(50))
    user_id = Column(String(100))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")

    __table_args__ = (
        CheckConstraint(f"type IN {ACTIVITY_TYPES}"),
        CheckConstraint("direction IN ('inbound', 'outbound') OR direction IS NULL"),
        Index('idx_activities_prospect_id', 'prospect_id'),
        Index('idx_activities_contact_id', 'contact_id'),
        Index('idx_activities_type', 'type'),
        Index('idx_activities_created_at', 'created_at'),
    )


class OutreachSequence(Base):
    """Track multi-step outreach campaigns."""
    __tablename__ = 'outreach_sequences'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    prospect_id = Column(String(32), ForeignKey('prospects.id'), nullable=False)
    contact_id = Column(String(32), ForeignKey('contacts.id'), nullable=False)

    # Sequence Info
    template_id = Column(String(32), nullable=False)
    tier = Column(String(5), nullable=False)

    # Status
    status = Column(String(20), nullable=False, default='pending')
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=False)

    # Timing
    started_at = Column(DateTime)
    paused_at = Column(DateTime)
    completed_at = Column(DateTime)
    next_step_at = Column(DateTime)

    # Results
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)

    # Approval (for A1 tier)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="outreach_sequences")
    contact = relationship("Contact", back_populates="outreach_sequences")

    __table_args__ = (
        CheckConstraint(f"status IN {SEQUENCE_STATUSES}"),
        CheckConstraint("tier IN ('A1', 'A2', 'B')"),
        Index('idx_outreach_sequences_prospect_id', 'prospect_id'),
        Index('idx_outreach_sequences_status', 'status'),
        Index('idx_outreach_sequences_next_step_at', 'next_step_at'),
    )


class OutreachTemplate(Base):
    """Email sequence templates by tier."""
    __tablename__ = 'outreach_templates'

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Template Info
    name = Column(String(100), nullable=False)
    tier = Column(String(5), nullable=False)
    step_number = Column(Integer, nullable=False)

    # Content
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)

    # Timing
    days_after_previous = Column(Integer, nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("tier IN ('A1', 'A2', 'B')"),
        Index('idx_outreach_templates_tier_step', 'tier', 'step_number', unique=True),
    )


class AgentRun(Base):
    """Execution history for all agents."""
    __tablename__ = 'agent_runs'

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Run Info
    agent_name = Column(String(50), nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Results
    status = Column(String(20), nullable=False, default='running')
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)

    # Errors
    error_message = Column(Text)
    error_traceback = Column(Text)

    # Metadata
    trigger = Column(String(50))

    # Relationships
    audit_logs = relationship("AgentAuditLog", back_populates="agent_run", lazy="dynamic")

    __table_args__ = (
        CheckConstraint(f"agent_name IN {AGENT_NAMES}"),
        CheckConstraint(f"status IN {AGENT_RUN_STATUSES}"),
        Index('idx_agent_runs_agent_name', 'agent_name'),
        Index('idx_agent_runs_started_at', 'started_at'),
        Index('idx_agent_runs_status', 'status'),
    )


class AgentAuditLog(Base):
    """Detailed action log for every agent operation."""
    __tablename__ = 'agent_audit_log'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    agent_run_id = Column(String(32), ForeignKey('agent_runs.id'))

    # Action Details
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)

    # Target
    prospect_id = Column(String(32), ForeignKey('prospects.id'))
    contact_id = Column(String(32), ForeignKey('contacts.id'))

    # Details
    details = Column(Text)  # JSON blob

    # Review
    requires_review = Column(Boolean, default=False)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(100))

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_agent_audit_log_agent_run_id', 'agent_run_id'),
        Index('idx_agent_audit_log_prospect_id', 'prospect_id'),
        Index('idx_agent_audit_log_requires_review', 'requires_review'),
        Index('idx_agent_audit_log_created_at', 'created_at'),
    )


class HygieneFlag(Base):
    """Issues requiring human review."""
    __tablename__ = 'hygiene_flags'

    id = Column(String(32), primary_key=True, default=generate_uuid)
    prospect_id = Column(String(32), ForeignKey('prospects.id'), nullable=False)

    # Flag Details
    flag_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default='info')
    message = Column(Text, nullable=False)
    suggested_action = Column(Text)

    # Resolution
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    resolution_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="hygiene_flags")

    __table_args__ = (
        CheckConstraint(f"flag_type IN {FLAG_TYPES}"),
        CheckConstraint(f"severity IN {FLAG_SEVERITIES}"),
        Index('idx_hygiene_flags_prospect_id', 'prospect_id'),
        Index('idx_hygiene_flags_resolved_at', 'resolved_at'),
        Index('idx_hygiene_flags_severity', 'severity'),
    )


class BidAlert(Base):
    """Tracked RFPs from bid portals."""
    __tablename__ = 'bid_alerts'

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Bid Info
    source = Column(String(50), nullable=False)
    external_id = Column(String(100))
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Organization
    organization_name = Column(String(255), nullable=False)
    state = Column(String(10))

    # Timing
    posted_date = Column(Date)
    due_date = Column(Date)

    # Matching
    matched_prospect_id = Column(String(32), ForeignKey('prospects.id'))
    match_confidence = Column(Float)

    # Status
    status = Column(String(20), nullable=False, default='new')
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(100))

    # Metadata
    source_url = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(f"source IN {BID_SOURCES}"),
        CheckConstraint(f"status IN {BID_STATUSES}"),
        Index('idx_bid_alerts_status', 'status'),
        Index('idx_bid_alerts_due_date', 'due_date'),
        Index('idx_bid_alerts_state', 'state'),
    )
