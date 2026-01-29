# Database Schema Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Define all database tables, relationships, and constraints for the Sportsbeams pipeline

---

## Overview

The database stores all prospect, contact, activity, and agent execution data. The schema is designed to support:

1. **Prospect lifecycle tracking** from identification through engagement
2. **Multi-contact relationships** (AD, facilities director, CFO per venue)
3. **Agent audit trails** for every automated action
4. **Scoring history** to track ICP changes over time
5. **Outreach sequence management** with approval workflows

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Prospect     │       │     Contact     │       │    Activity     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │───┐   │ id              │───┐   │ id              │
│ name            │   │   │ prospect_id  ◄──┼───┘   │ prospect_id  ◄──┼───┐
│ venue_type      │   │   │ name            │       │ contact_id      │   │
│ state           │   └──▶│ title           │       │ type            │   │
│ classification  │       │ email           │       │ description     │   │
│ status          │       │ phone           │       │ agent_id        │   │
│ tier            │       │ linkedin_url    │       │ created_at      │   │
│ icp_score       │       │ is_primary      │       └─────────────────┘   │
│ ...             │       │ created_at      │                             │
└─────────────────┘       └─────────────────┘                             │
        │                                                                  │
        │         ┌─────────────────┐       ┌─────────────────┐           │
        │         │  ProspectScore  │       │ OutreachSequence│           │
        │         ├─────────────────┤       ├─────────────────┤           │
        │         │ id              │       │ id              │           │
        └────────▶│ prospect_id     │       │ prospect_id  ◄──┼───────────┘
                  │ dimension       │       │ contact_id      │
                  │ score           │       │ template_id     │
                  │ notes           │       │ status          │
                  │ scored_at       │       │ current_step    │
                  │ scored_by       │       │ started_at      │
                  └─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    AgentRun     │       │ AgentAuditLog   │       │  HygieneFlag    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │───┐   │ id              │       │ id              │
│ agent_name      │   │   │ agent_run_id ◄──┼───┘   │ prospect_id     │
│ started_at      │   │   │ prospect_id     │       │ flag_type       │
│ completed_at    │   │   │ action          │       │ severity        │
│ status          │   │   │ details         │       │ message         │
│ records_processed   │   │ created_at      │       │ resolved_at     │
│ error_message   │   └──▶└─────────────────┘       │ resolved_by     │
└─────────────────┘                                 └─────────────────┘
```

---

## Table Definitions

### prospects

Primary table for athletic venues (schools/colleges).

```sql
CREATE TABLE prospects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Basic Info
    name TEXT NOT NULL,                          -- "Ohio State University" or "Mason High School"
    venue_type TEXT NOT NULL,                    -- college_d1, college_d2, college_d3, college_naia, high_school_6a, high_school_5a, etc.
    state TEXT NOT NULL,                         -- OH, IN, PA, KY, IL
    city TEXT,
    address TEXT,
    
    -- Classification (for high schools)
    classification TEXT,                         -- 6A, 5A, 4A, 3A, etc.
    conference TEXT,                             -- Athletic conference name
    enrollment INTEGER,                          -- Student count
    
    -- Facility Info
    primary_sport TEXT,                          -- football, baseball, multi_sport
    stadium_name TEXT,
    seating_capacity INTEGER,
    current_lighting_type TEXT,                  -- metal_halide, early_led, modern_led, unknown
    current_lighting_age_years INTEGER,
    has_night_games BOOLEAN DEFAULT TRUE,
    broadcast_requirements TEXT,                 -- none, local_streaming, conference_network, espn
    
    -- Pipeline Status
    status TEXT NOT NULL DEFAULT 'identified',   -- identified, needs_scoring, scored, needs_research, research_complete, ready_for_outreach, outreach_active, engaged, nurture, deprioritized
    tier TEXT,                                   -- A1, A2, B, C, D
    icp_score INTEGER,                           -- 0-100 normalized score
    
    -- Research
    constraint_hypothesis TEXT,                  -- Primary pain point identified
    value_proposition TEXT,                      -- Tailored pitch
    research_notes TEXT,
    
    -- Timing
    estimated_project_timeline TEXT,             -- immediate, within_6_months, within_12_months, 12_plus_months, unknown
    budget_cycle_month INTEGER,                  -- Fiscal year start month (1-12)
    
    -- Source Tracking
    source TEXT,                                 -- manual, bid_portal, directory_import, referral, linkedin
    source_url TEXT,
    source_date DATE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Constraints
    CHECK (venue_type IN ('college_d1', 'college_d2', 'college_d3', 'college_naia', 'high_school_6a', 'high_school_5a', 'high_school_4a', 'high_school_3a', 'high_school_other')),
    CHECK (state IN ('OH', 'IN', 'PA', 'KY', 'IL', 'OTHER')),
    CHECK (status IN ('identified', 'needs_scoring', 'scored', 'needs_research', 'research_complete', 'ready_for_outreach', 'outreach_active', 'engaged', 'nurture', 'deprioritized')),
    CHECK (tier IN ('A1', 'A2', 'B', 'C', 'D') OR tier IS NULL)
);

CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_tier ON prospects(tier);
CREATE INDEX idx_prospects_state ON prospects(state);
CREATE INDEX idx_prospects_venue_type ON prospects(venue_type);
```

### contacts

People associated with prospects.

```sql
CREATE TABLE contacts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    
    -- Basic Info
    name TEXT NOT NULL,
    title TEXT,                                  -- Athletic Director, Facilities Director, CFO, etc.
    role TEXT,                                   -- decision_maker, influencer, champion, blocker
    
    -- Contact Info
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    
    -- Engagement
    is_primary BOOLEAN DEFAULT FALSE,            -- Primary contact for this prospect
    last_contacted_at TIMESTAMP,
    last_response_at TIMESTAMP,
    engagement_score INTEGER DEFAULT 0,          -- Calculated from activities
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CHECK (role IN ('decision_maker', 'influencer', 'champion', 'blocker', 'unknown') OR role IS NULL)
);

CREATE INDEX idx_contacts_prospect_id ON contacts(prospect_id);
CREATE INDEX idx_contacts_email ON contacts(email);
```

### prospect_scores

Individual dimension scores for ICP calculation.

```sql
CREATE TABLE prospect_scores (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    
    -- Score Details
    dimension TEXT NOT NULL,                     -- venue_type, geography, budget_signals, etc.
    score INTEGER NOT NULL,                      -- 1-10
    weight INTEGER NOT NULL,                     -- Dimension weight for calculation
    notes TEXT,                                  -- Rationale for score
    
    -- Metadata
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scored_by TEXT,                              -- agent:hygiene or user:email
    
    CHECK (dimension IN ('venue_type', 'geography', 'budget_signals', 'current_lighting_age', 'night_game_frequency', 'broadcast_requirements', 'decision_maker_access', 'project_timeline')),
    CHECK (score BETWEEN 1 AND 10),
    CHECK (weight BETWEEN 1 AND 5)
);

CREATE INDEX idx_prospect_scores_prospect_id ON prospect_scores(prospect_id);
CREATE UNIQUE INDEX idx_prospect_scores_unique ON prospect_scores(prospect_id, dimension, scored_at);
```

### activities

All interactions and events related to prospects.

```sql
CREATE TABLE activities (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    contact_id TEXT REFERENCES contacts(id),
    
    -- Activity Details
    type TEXT NOT NULL,                          -- email_sent, email_received, call, meeting, note, status_change, score_change, research_completed
    direction TEXT,                              -- inbound, outbound (for communications)
    subject TEXT,
    description TEXT,
    
    -- For emails
    email_template_id TEXT,
    email_sequence_step INTEGER,
    
    -- Attribution
    agent_id TEXT,                               -- Which agent created this
    user_id TEXT,                                -- Which user (if manual)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (type IN ('email_sent', 'email_received', 'email_opened', 'email_clicked', 'call', 'meeting', 'note', 'status_change', 'score_change', 'research_completed', 'outreach_started', 'outreach_paused', 'outreach_completed')),
    CHECK (direction IN ('inbound', 'outbound') OR direction IS NULL)
);

CREATE INDEX idx_activities_prospect_id ON activities(prospect_id);
CREATE INDEX idx_activities_contact_id ON activities(contact_id);
CREATE INDEX idx_activities_type ON activities(type);
CREATE INDEX idx_activities_created_at ON activities(created_at);
```

### outreach_sequences

Track multi-step outreach campaigns.

```sql
CREATE TABLE outreach_sequences (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    contact_id TEXT NOT NULL REFERENCES contacts(id),
    
    -- Sequence Info
    template_id TEXT NOT NULL,                   -- Reference to sequence template
    tier TEXT NOT NULL,                          -- A1, A2, B (determines sequence type)
    
    -- Status
    status TEXT NOT NULL DEFAULT 'pending',      -- pending, active, paused, completed, stopped
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    
    -- Timing
    started_at TIMESTAMP,
    paused_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_step_at TIMESTAMP,
    
    -- Results
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    replies_received INTEGER DEFAULT 0,
    
    -- Approval (for A1 tier)
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by TEXT,
    approved_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (status IN ('pending', 'active', 'paused', 'completed', 'stopped')),
    CHECK (tier IN ('A1', 'A2', 'B'))
);

CREATE INDEX idx_outreach_sequences_prospect_id ON outreach_sequences(prospect_id);
CREATE INDEX idx_outreach_sequences_status ON outreach_sequences(status);
CREATE INDEX idx_outreach_sequences_next_step_at ON outreach_sequences(next_step_at);
```

### outreach_templates

Email sequence templates by tier.

```sql
CREATE TABLE outreach_templates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Template Info
    name TEXT NOT NULL,
    tier TEXT NOT NULL,                          -- A1, A2, B
    step_number INTEGER NOT NULL,
    
    -- Content
    subject_template TEXT NOT NULL,              -- With {{variables}}
    body_template TEXT NOT NULL,                 -- With {{variables}}
    
    -- Timing
    days_after_previous INTEGER NOT NULL,        -- Days to wait after previous step
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (tier IN ('A1', 'A2', 'B'))
);

CREATE UNIQUE INDEX idx_outreach_templates_unique ON outreach_templates(tier, step_number);
```

### agent_runs

Execution history for all agents.

```sql
CREATE TABLE agent_runs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Run Info
    agent_name TEXT NOT NULL,                    -- prospector, hygiene, researcher, outreach, orchestrator
    
    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    status TEXT NOT NULL DEFAULT 'running',      -- running, completed, failed
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    
    -- Errors
    error_message TEXT,
    error_traceback TEXT,
    
    -- Metadata
    trigger TEXT,                                -- scheduled, manual, event
    
    CHECK (agent_name IN ('prospector', 'hygiene', 'researcher', 'outreach', 'orchestrator')),
    CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_agent_runs_agent_name ON agent_runs(agent_name);
CREATE INDEX idx_agent_runs_started_at ON agent_runs(started_at);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
```

### agent_audit_log

Detailed action log for every agent operation.

```sql
CREATE TABLE agent_audit_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_run_id TEXT REFERENCES agent_runs(id),
    
    -- Action Details
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,                        -- prospect_created, prospect_scored, research_completed, email_drafted, etc.
    
    -- Target
    prospect_id TEXT REFERENCES prospects(id),
    contact_id TEXT REFERENCES contacts(id),
    
    -- Details
    details TEXT,                                -- JSON blob with action-specific data
    
    -- Review
    requires_review BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_audit_log_agent_run_id ON agent_audit_log(agent_run_id);
CREATE INDEX idx_agent_audit_log_prospect_id ON agent_audit_log(prospect_id);
CREATE INDEX idx_agent_audit_log_requires_review ON agent_audit_log(requires_review);
CREATE INDEX idx_agent_audit_log_created_at ON agent_audit_log(created_at);
```

### hygiene_flags

Issues requiring human review.

```sql
CREATE TABLE hygiene_flags (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    
    -- Flag Details
    flag_type TEXT NOT NULL,                     -- missing_contact, missing_email, stale_data, score_anomaly, duplicate_suspect
    severity TEXT NOT NULL DEFAULT 'info',       -- info, warning, critical
    message TEXT NOT NULL,
    suggested_action TEXT,
    
    -- Resolution
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (flag_type IN ('missing_contact', 'missing_email', 'stale_data', 'score_anomaly', 'duplicate_suspect', 'data_quality', 'outreach_blocked')),
    CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX idx_hygiene_flags_prospect_id ON hygiene_flags(prospect_id);
CREATE INDEX idx_hygiene_flags_resolved_at ON hygiene_flags(resolved_at);
CREATE INDEX idx_hygiene_flags_severity ON hygiene_flags(severity);
```

### bid_alerts

Tracked RFPs from bid portals.

```sql
CREATE TABLE bid_alerts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Bid Info
    source TEXT NOT NULL,                        -- bidnet, onvia, public_purchase
    external_id TEXT,                            -- ID from source system
    title TEXT NOT NULL,
    description TEXT,
    
    -- Organization
    organization_name TEXT NOT NULL,
    state TEXT,
    
    -- Timing
    posted_date DATE,
    due_date DATE,
    
    -- Matching
    matched_prospect_id TEXT REFERENCES prospects(id),
    match_confidence REAL,                       -- 0-1
    
    -- Status
    status TEXT NOT NULL DEFAULT 'new',          -- new, reviewed, matched, not_relevant
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,
    
    -- Metadata
    source_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (source IN ('bidnet', 'onvia', 'public_purchase', 'manual')),
    CHECK (status IN ('new', 'reviewed', 'matched', 'not_relevant'))
);

CREATE INDEX idx_bid_alerts_status ON bid_alerts(status);
CREATE INDEX idx_bid_alerts_due_date ON bid_alerts(due_date);
CREATE INDEX idx_bid_alerts_state ON bid_alerts(state);
```

---

## Seed Data

### Outreach Templates (Initial Set)

```sql
-- A1 Tier (High-touch, 4 steps)
INSERT INTO outreach_templates (id, name, tier, step_number, subject_template, body_template, days_after_previous) VALUES
('a1-1', 'A1 Initial Outreach', 'A1', 1, '{{stadium_name}} Lighting - Quick Question', 'Hi {{first_name}},\n\nI noticed {{school_name}} has been {{trigger_observation}}. Given the timing, I wanted to reach out about your field lighting.\n\n{{constraint_hypothesis}}\n\nWould a 15-minute call this week make sense to see if we can help?\n\nBest,\n{{sender_name}}', 0),
('a1-2', 'A1 Case Study Follow-up', 'A1', 2, 'How {{similar_school}} solved their lighting challenge', 'Hi {{first_name}},\n\nQuick follow-up on my note about {{stadium_name}}.\n\nI thought you might find this relevant - {{similar_school}} faced a similar situation with {{shared_challenge}}. Here''s what they did: {{case_study_link}}\n\nWorth a conversation?\n\nBest,\n{{sender_name}}', 4),
('a1-3', 'A1 Value Add', 'A1', 3, 'Complimentary photometric study for {{school_name}}', 'Hi {{first_name}},\n\nI wanted to offer something concrete - we''d be happy to do a complimentary photometric study of {{stadium_name}} to show exactly what modern LED lighting could look like.\n\nNo commitment, just useful data for whenever your timeline makes sense.\n\nInterested?\n\nBest,\n{{sender_name}}', 5),
('a1-4', 'A1 Break-up', 'A1', 4, 'Closing the loop on {{school_name}} lighting', 'Hi {{first_name}},\n\nI''ve reached out a few times about lighting for {{stadium_name}} and haven''t heard back - totally understand if the timing isn''t right.\n\nI''ll step back for now, but if lighting comes up in the future, I''d welcome the chance to help. We''ve done great work with similar programs like {{similar_school}}.\n\nWishing you a great season ahead.\n\nBest,\n{{sender_name}}', 7);

-- A2 Tier (Standard, 3 steps)
INSERT INTO outreach_templates (id, name, tier, step_number, subject_template, body_template, days_after_previous) VALUES
('a2-1', 'A2 Initial Outreach', 'A2', 1, 'LED Lighting for {{school_name}} Athletics', 'Hi {{first_name}},\n\nI''m reaching out to athletic directors at {{classification}} programs in {{state}} about field lighting upgrades.\n\n{{value_proposition}}\n\nWould it make sense to connect briefly about your facilities roadmap?\n\nBest,\n{{sender_name}}', 0),
('a2-2', 'A2 Follow-up', 'A2', 2, 'Following up - {{school_name}} lighting', 'Hi {{first_name}},\n\nQuick follow-up on my note about lighting for {{school_name}}.\n\nI''ve attached a case study from {{similar_school}} that might be relevant to your situation.\n\nWorth a quick call?\n\nBest,\n{{sender_name}}', 5),
('a2-3', 'A2 Break-up', 'A2', 3, 'One more note on {{school_name}} lighting', 'Hi {{first_name}},\n\nI''ll keep this brief - I''ve reached out about lighting for {{stadium_name}} and understand if the timing isn''t right.\n\nIf it ever comes up, we''d love to help. Feel free to reach out anytime.\n\nBest,\n{{sender_name}}', 7);

-- B Tier (Nurture, 2 steps)
INSERT INTO outreach_templates (id, name, tier, step_number, subject_template, body_template, days_after_previous) VALUES
('b-1', 'B Initial Outreach', 'B', 1, 'Resource: LED Lighting ROI Calculator', 'Hi {{first_name}},\n\nI wanted to share a resource that might be useful when you''re planning future facility upgrades - our LED Lighting ROI Calculator.\n\nIt helps estimate energy savings and payback period for athletic lighting projects: {{roi_calculator_link}}\n\nNo pitch - just a useful tool. Let me know if you have any questions.\n\nBest,\n{{sender_name}}', 0),
('b-2', 'B Quarterly Check-in', 'B', 2, 'Checking in - {{school_name}} facilities planning', 'Hi {{first_name}},\n\nHope the season is going well at {{school_name}}.\n\nI wanted to check in on your facilities roadmap - any lighting projects on the horizon?\n\nEither way, happy to be a resource if questions come up.\n\nBest,\n{{sender_name}}', 90);
```

---

## Migration Strategy

1. **Initial Setup:** Run all CREATE TABLE statements
2. **Seed Data:** Insert outreach templates
3. **Import Existing Data:** If migrating from spreadsheets or other systems, create import scripts

### SQLAlchemy Models

Create corresponding SQLAlchemy models in `database/models.py` that mirror these table definitions. Use:
- UUID strings for primary keys (generated in Python)
- DateTime fields with timezone awareness
- Proper relationship definitions
- Column defaults matching SQL defaults

---

## Indexes and Performance

Key queries to optimize:

1. **Prospects by status and tier:** `WHERE status = ? AND tier = ?`
2. **Prospects needing action:** `WHERE status IN ('needs_scoring', 'needs_research', 'ready_for_outreach')`
3. **Recent activities:** `WHERE created_at > ? ORDER BY created_at DESC`
4. **Pending outreach:** `WHERE status = 'active' AND next_step_at < ?`
5. **Unresolved flags:** `WHERE resolved_at IS NULL ORDER BY severity, created_at`

All critical indexes are defined in the CREATE TABLE statements above.

---

## Related Documents

- [Prospector Agent](02-prospector-agent.md) - Creates prospects
- [Hygiene Agent](03-hygiene-agent.md) - Scores prospects, creates flags
- [Researcher Agent](04-researcher-agent.md) - Updates research fields
- [Outreach Agent](05-outreach-agent.md) - Manages sequences
