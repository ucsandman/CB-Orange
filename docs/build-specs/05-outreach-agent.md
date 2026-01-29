# Outreach Agent Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the agent that executes email sequences for qualified prospects

---

## Overview

The Outreach Agent manages multi-step email sequences for prospects who have completed research. It drafts personalized emails, manages timing, tracks engagement, and enforces human approval for high-priority prospects.

### Responsibilities

1. **Sequence Management** - Start, pause, resume, and complete outreach sequences
2. **Email Drafting** - Generate personalized emails from templates
3. **Timing Control** - Send emails at appropriate intervals
4. **Engagement Tracking** - Track opens, clicks, and replies
5. **Human Approval** - Enforce approval workflow for A1 tier

### Non-Responsibilities

- Research and personalization data (Researcher Agent)
- Contact discovery (separate utility)
- CRM sync (separate integration)

---

## Sequence Types by Tier

### A1 Tier (High-Touch)

**Characteristics:**
- 4-step sequence
- Highly personalized with video option
- Requires human approval before each send
- 3-4 days between touches
- Includes case study and photometric study offer

```
Step 1: Personalized intro + constraint hypothesis
Step 2: Case study from similar venue
Step 3: Offer complimentary photometric study
Step 4: Polite break-up with open door
```

### A2 Tier (Standard)

**Characteristics:**
- 3-step sequence
- Personalized but templated
- Auto-send enabled (no approval required)
- 5-7 days between touches
- Focus on ROI and case studies

```
Step 1: Standard intro + value proposition
Step 2: Case study follow-up
Step 3: Break-up with resource offer
```

### B Tier (Nurture)

**Characteristics:**
- 2-step sequence
- Light touch
- Auto-send enabled
- 90-day interval for quarterly check-in
- Focus on being helpful, not selling

```
Step 1: Resource share (ROI calculator)
Step 2: Quarterly check-in
```

---

## Email Personalization

### Template Variables

```python
TEMPLATE_VARIABLES = {
    # Prospect fields
    '{{school_name}}': 'prospect.name',
    '{{stadium_name}}': 'prospect.stadium_name',
    '{{state}}': 'prospect.state',
    '{{city}}': 'prospect.city',
    '{{classification}}': 'prospect.classification',
    '{{venue_type}}': 'prospect.venue_type',
    
    # Contact fields
    '{{first_name}}': 'contact.first_name',
    '{{last_name}}': 'contact.last_name',
    '{{title}}': 'contact.title',
    
    # Research fields
    '{{constraint_hypothesis}}': 'prospect.constraint_hypothesis',
    '{{value_proposition}}': 'prospect.value_proposition',
    '{{estimated_impact}}': 'research.estimated_annual_impact',
    
    # Dynamic content
    '{{similar_school}}': 'matched_case_study.school_name',
    '{{shared_challenge}}': 'matched_case_study.challenge',
    '{{case_study_link}}': 'matched_case_study.url',
    '{{trigger_observation}}': 'research.trigger_observation',
    
    # Sender fields
    '{{sender_name}}': 'sender.name',
    '{{sender_title}}': 'sender.title',
    '{{sender_email}}': 'sender.email',
    '{{sender_phone}}': 'sender.phone',
    
    # Links
    '{{roi_calculator_link}}': 'config.roi_calculator_url',
    '{{booking_link}}': 'config.calendar_booking_url',
}
```

### Case Study Matching

```python
class CaseStudyMatcher:
    """
    Match prospects to relevant case studies.
    
    Matching criteria (in priority order):
    1. Same venue type (college_d1 → college_d1 case study)
    2. Same state or region
    3. Similar constraint/challenge
    4. Similar sport
    """
    
    CASE_STUDIES = [
        {
            'id': 'texas_am',
            'school_name': 'Texas A&M',
            'venue_type': 'college_d1',
            'state': 'TX',
            'challenge': 'First fully color-changing stadium in college football',
            'url': 'https://sportsbeams.com/projects/texas-am',
            'tags': ['rgb', 'broadcast', 'game_day_experience'],
        },
        {
            'id': 'ford_amphitheater',
            'school_name': 'Ford Amphitheater',
            'venue_type': 'music_venue',
            'state': 'CO',
            'challenge': 'Concert lighting with emergency and crowd illumination',
            'url': 'https://sportsbeams.com/projects/ford-amphitheater',
            'tags': ['entertainment', 'rgb', 'safety'],
        },
        {
            'id': 'cedar_crest',
            'school_name': 'Cedar Crest Community Center',
            'venue_type': 'high_school',
            'state': 'TX',
            'challenge': 'Multi-sport facility with integrated football and baseball',
            'url': 'https://sportsbeams.com/projects/cedar-crest',
            'tags': ['high_school', 'multi_sport', 'community'],
        },
        # Add more case studies as available
    ]
    
    def match(self, prospect: Prospect) -> dict:
        """Find best matching case study for prospect."""
        scores = []
        
        for cs in self.CASE_STUDIES:
            score = 0
            
            # Venue type match
            if self._venue_type_match(prospect.venue_type, cs['venue_type']):
                score += 10
            
            # Same state
            if prospect.state == cs['state']:
                score += 5
            
            # Same region
            if self._same_region(prospect.state, cs['state']):
                score += 2
            
            # Challenge match
            if prospect.constraint_hypothesis:
                for tag in cs['tags']:
                    if tag in prospect.constraint_hypothesis.lower():
                        score += 3
            
            scores.append((score, cs))
        
        # Return highest scoring
        scores.sort(reverse=True, key=lambda x: x[0])
        return scores[0][1] if scores else None
```

---

## Agent Implementation

### File Structure

```
agents/outreach/
├── __init__.py
├── agent.py              # Main OutreachAgent class
├── sequence_manager.py   # Manage sequence state
├── email_drafter.py      # Draft emails from templates
├── email_sender.py       # Send via SMTP/API
├── engagement_tracker.py # Track opens/clicks/replies
├── approval_workflow.py  # Human approval logic
├── case_study_matcher.py # Match case studies
└── config.py
```

### Main Agent Class

```python
# agents/outreach/agent.py

from agents.base import BaseAgent
from agents.outreach.sequence_manager import SequenceManager
from agents.outreach.email_drafter import EmailDrafter
from agents.outreach.email_sender import EmailSender
from agents.outreach.engagement_tracker import EngagementTracker
from database.models import Prospect, Contact, OutreachSequence, Activity
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OutreachAgent(BaseAgent):
    """
    Agent that executes outreach sequences.
    
    Run modes:
    - process_ready: Start sequences for prospects ready for outreach
    - execute_pending: Send emails that are due
    - check_engagement: Process engagement events (opens, clicks, replies)
    """
    
    name = "outreach"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.sequence_manager = SequenceManager(db_session)
        self.drafter = EmailDrafter()
        self.sender = EmailSender()
        self.tracker = EngagementTracker(db_session)
    
    def run_cycle(self) -> dict:
        """Run a full outreach cycle."""
        results = {
            'sequences_started': 0,
            'emails_sent': 0,
            'awaiting_approval': 0,
            'errors': [],
        }
        
        # 1. Start sequences for ready prospects
        results['sequences_started'] = self._start_ready_sequences()
        
        # 2. Execute pending sends
        send_results = self._execute_pending_sends()
        results['emails_sent'] = send_results['sent']
        results['awaiting_approval'] = send_results['awaiting_approval']
        
        # 3. Process engagement events
        self._process_engagement()
        
        return results
    
    def _start_ready_sequences(self) -> int:
        """Start sequences for prospects in 'research_complete' status."""
        prospects = self.db.query(Prospect).filter(
            Prospect.status == 'research_complete',
            Prospect.deleted_at.is_(None)
        ).all()
        
        started = 0
        
        for prospect in prospects:
            # Get primary contact
            primary_contact = self.db.query(Contact).filter(
                Contact.prospect_id == prospect.id,
                Contact.is_primary == True,
                Contact.email.isnot(None),
                Contact.deleted_at.is_(None)
            ).first()
            
            if not primary_contact:
                logger.warning(f"No primary contact with email for {prospect.id}")
                continue
            
            # Create sequence
            sequence = self.sequence_manager.create_sequence(
                prospect=prospect,
                contact=primary_contact,
            )
            
            # Update prospect status
            prospect.status = 'outreach_active'
            
            self.log_action(
                action="sequence_started",
                prospect_id=prospect.id,
                details={
                    "sequence_id": sequence.id,
                    "tier": sequence.tier,
                    "contact": primary_contact.email,
                }
            )
            
            started += 1
        
        self.db.commit()
        return started
    
    def _execute_pending_sends(self) -> dict:
        """Send emails that are due."""
        now = datetime.utcnow()
        
        # Find sequences with pending sends
        sequences = self.db.query(OutreachSequence).filter(
            OutreachSequence.status == 'active',
            OutreachSequence.next_step_at <= now,
        ).all()
        
        sent = 0
        awaiting_approval = 0
        
        for sequence in sequences:
            prospect = self.db.query(Prospect).get(sequence.prospect_id)
            contact = self.db.query(Contact).get(sequence.contact_id)
            
            # Check if A1 tier needs approval
            if sequence.tier == 'A1' and not sequence.approved_at:
                # Draft email for approval
                draft = self.drafter.draft(
                    sequence=sequence,
                    prospect=prospect,
                    contact=contact,
                )
                
                # Store draft and flag for approval
                self._queue_for_approval(sequence, draft)
                awaiting_approval += 1
                continue
            
            # Draft and send
            email = self.drafter.draft(
                sequence=sequence,
                prospect=prospect,
                contact=contact,
            )
            
            try:
                self.sender.send(email, contact.email)
                
                # Update sequence
                sequence.emails_sent += 1
                sequence.current_step += 1
                
                if sequence.current_step >= sequence.total_steps:
                    sequence.status = 'completed'
                    sequence.completed_at = now
                else:
                    # Schedule next step
                    days_until_next = self._get_step_delay(sequence.tier, sequence.current_step)
                    sequence.next_step_at = now + timedelta(days=days_until_next)
                
                # Log activity
                activity = Activity(
                    prospect_id=sequence.prospect_id,
                    contact_id=sequence.contact_id,
                    type='email_sent',
                    direction='outbound',
                    subject=email['subject'],
                    description=f"Sequence step {sequence.current_step} of {sequence.total_steps}",
                    agent_id=self.name,
                )
                self.db.add(activity)
                
                sent += 1
                
            except Exception as e:
                logger.error(f"Failed to send email for sequence {sequence.id}: {e}")
        
        self.db.commit()
        return {'sent': sent, 'awaiting_approval': awaiting_approval}
    
    def _get_step_delay(self, tier: str, current_step: int) -> int:
        """Get days to wait before next step."""
        DELAYS = {
            'A1': [0, 4, 5, 7],    # Initial, then 4, 5, 7 days
            'A2': [0, 5, 7],       # Initial, then 5, 7 days
            'B': [0, 90],          # Initial, then 90 days (quarterly)
        }
        delays = DELAYS.get(tier, [0, 7])
        return delays[min(current_step, len(delays) - 1)]
    
    def _queue_for_approval(self, sequence: OutreachSequence, draft: dict) -> None:
        """Queue an email for human approval."""
        sequence.requires_approval = True
        # Store draft in a pending_emails table or similar
        # Notify via WebSocket that approval is needed
        self.emit_event("approval_needed", {
            "sequence_id": sequence.id,
            "prospect_id": sequence.prospect_id,
            "subject": draft['subject'],
            "body_preview": draft['body'][:200],
        })
    
    def approve_send(self, sequence_id: str, approved_by: str) -> bool:
        """Approve a pending send for A1 tier."""
        sequence = self.db.query(OutreachSequence).get(sequence_id)
        
        if not sequence or sequence.tier != 'A1':
            return False
        
        sequence.approved_by = approved_by
        sequence.approved_at = datetime.utcnow()
        
        # Will be picked up on next execute_pending_sends cycle
        self.db.commit()
        return True
    
    def _process_engagement(self) -> None:
        """Process engagement events from email tracking."""
        # Check for opens, clicks, replies via webhook or polling
        events = self.tracker.get_new_events()
        
        for event in events:
            self.tracker.process_event(event)
```

### Email Drafter

```python
# agents/outreach/email_drafter.py

from database.models import OutreachTemplate, Prospect, Contact, OutreachSequence
from agents.outreach.case_study_matcher import CaseStudyMatcher

class EmailDrafter:
    """Draft personalized emails from templates."""
    
    def __init__(self):
        self.case_study_matcher = CaseStudyMatcher()
    
    def draft(self, sequence: OutreachSequence, prospect: Prospect, contact: Contact) -> dict:
        """
        Draft an email for the current sequence step.
        
        Returns:
            {
                'subject': 'Personalized subject line',
                'body': 'Personalized email body',
                'template_id': 'template used',
            }
        """
        # Get template for this tier and step
        template = self._get_template(sequence.tier, sequence.current_step + 1)
        
        # Build context for variable replacement
        context = self._build_context(prospect, contact)
        
        # Replace variables
        subject = self._replace_variables(template.subject_template, context)
        body = self._replace_variables(template.body_template, context)
        
        return {
            'subject': subject,
            'body': body,
            'template_id': template.id,
        }
    
    def _build_context(self, prospect: Prospect, contact: Contact) -> dict:
        """Build context dictionary for template variables."""
        # Parse first name from full name
        first_name = contact.name.split()[0] if contact.name else ''
        
        # Get matching case study
        case_study = self.case_study_matcher.match(prospect)
        
        # Parse research notes if available
        research = {}
        if prospect.research_notes:
            try:
                research = json.loads(prospect.research_notes)
            except:
                pass
        
        return {
            # Prospect
            'school_name': prospect.name,
            'stadium_name': prospect.stadium_name or 'your stadium',
            'state': prospect.state,
            'city': prospect.city or '',
            'classification': prospect.classification or '',
            'venue_type': self._format_venue_type(prospect.venue_type),
            
            # Contact
            'first_name': first_name,
            'last_name': contact.name.split()[-1] if contact.name else '',
            'title': contact.title or '',
            
            # Research
            'constraint_hypothesis': self._format_constraint(prospect.constraint_hypothesis),
            'value_proposition': prospect.value_proposition or '',
            'trigger_observation': research.get('trigger_observation', ''),
            
            # Case study
            'similar_school': case_study['school_name'] if case_study else '',
            'shared_challenge': case_study['challenge'] if case_study else '',
            'case_study_link': case_study['url'] if case_study else '',
            
            # Sender (from config)
            'sender_name': 'Sales Rep',  # TODO: Get from config
            'sender_title': 'Sales Representative',
            'sender_email': 'sales@sportsbeams.com',
            'sender_phone': '888-905-6680',
            
            # Links
            'roi_calculator_link': 'https://sportsbeams.com/roi-calculator',
            'booking_link': 'https://calendly.com/sportsbeams',
        }
    
    def _replace_variables(self, template: str, context: dict) -> str:
        """Replace {{variable}} placeholders with values."""
        result = template
        for key, value in context.items():
            result = result.replace(f'{{{{{key}}}}}', str(value or ''))
        return result
    
    def _format_venue_type(self, venue_type: str) -> str:
        """Format venue type for display."""
        FORMATS = {
            'college_d1': 'Division I',
            'college_d2': 'Division II',
            'college_d3': 'Division III',
            'high_school_6a': '6A',
            'high_school_5a': '5A',
        }
        return FORMATS.get(venue_type, venue_type)
    
    def _format_constraint(self, constraint: str) -> str:
        """Format constraint for conversational use."""
        if not constraint:
            return ''
        
        FORMATS = {
            'energy_cost_burden': "I noticed your facility may be dealing with high energy costs from older lighting",
            'maintenance_reliability': "Given the age of your current fixtures, maintenance is probably becoming a challenge",
            'night_game_capacity': "It looks like you might benefit from better lighting for night events",
            'broadcast_quality': "With your broadcast requirements, lighting quality is critical",
            'recruiting_disadvantage': "In competitive recruiting, facilities make a difference",
        }
        return FORMATS.get(constraint, f"I noticed {constraint}")
```

---

## Engagement Tracking

### Webhook Handler

```python
# api/routes/webhooks.py

from fastapi import APIRouter, Request
from agents.outreach.engagement_tracker import EngagementTracker

router = APIRouter(prefix="/webhooks")

@router.post("/email/open")
async def track_open(request: Request):
    """Handle email open tracking pixel."""
    data = await request.json()
    tracker = EngagementTracker(get_db())
    tracker.record_open(data['email_id'])
    return {"status": "ok"}

@router.post("/email/click")
async def track_click(request: Request):
    """Handle email link click."""
    data = await request.json()
    tracker = EngagementTracker(get_db())
    tracker.record_click(data['email_id'], data['link_url'])
    return {"status": "ok"}

@router.post("/email/reply")
async def track_reply(request: Request):
    """Handle inbound reply (from email provider webhook)."""
    data = await request.json()
    tracker = EngagementTracker(get_db())
    tracker.record_reply(data)
    return {"status": "ok"}
```

---

## API Endpoints

```python
# api/routes/outreach.py

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])

@router.post("/run")
async def run_outreach(background_tasks: BackgroundTasks):
    """Run full outreach cycle."""
    background_tasks.add_task(run_outreach_task)
    return {"status": "started"}

@router.get("/sequences")
async def list_sequences(
    status: str = None,
    tier: str = None,
    limit: int = 50
):
    """List outreach sequences."""
    pass

@router.get("/sequences/{sequence_id}")
async def get_sequence(sequence_id: str):
    """Get sequence details."""
    pass

@router.post("/sequences/{sequence_id}/pause")
async def pause_sequence(sequence_id: str):
    """Pause an active sequence."""
    pass

@router.post("/sequences/{sequence_id}/resume")
async def resume_sequence(sequence_id: str):
    """Resume a paused sequence."""
    pass

@router.post("/sequences/{sequence_id}/approve")
async def approve_sequence(sequence_id: str, approved_by: str):
    """Approve A1 tier email for sending."""
    pass

@router.get("/pending-approvals")
async def list_pending_approvals():
    """List sequences awaiting approval."""
    pass
```

---

## Testing

### Test Cases

1. **Sequence Creation**
   - Correct tier assigned based on prospect
   - Correct total steps for tier
   - Next step scheduled correctly

2. **Email Drafting**
   - All variables replaced
   - Case study matched appropriately
   - No template errors

3. **Approval Workflow**
   - A1 tier requires approval
   - A2/B tier auto-sends
   - Approval unblocks send

4. **Engagement Tracking**
   - Opens recorded
   - Clicks recorded with URL
   - Replies stop sequence

---

## Related Documents

- [Database Schema](01-database-schema.md) - OutreachSequence and template tables
- [Researcher Agent](04-researcher-agent.md) - Provides personalization data
- [Orchestrator Agent](06-orchestrator-agent.md) - Monitors outreach health
- [Dashboard](07-dashboard.md) - Approval UI
