# Hygiene Agent Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the agent that scores prospects against ICP criteria and assigns tiers

---

## Overview

The Hygiene Agent is responsible for evaluating prospects against the Ideal Customer Profile (ICP) and maintaining data quality. It runs automatically when new prospects are created and periodically to rescore existing prospects.

### Responsibilities

1. **ICP Scoring** - Calculate scores across 8 dimensions
2. **Tier Assignment** - Assign A1/A2/B/C/D tiers based on total score
3. **Data Quality Checks** - Flag missing or inconsistent data
4. **Staleness Detection** - Identify prospects that need re-engagement
5. **State Transitions** - Move prospects through pipeline states

### Non-Responsibilities

- Finding new prospects (Prospector Agent)
- Deep research (Researcher Agent)
- Sending outreach (Outreach Agent)

---

## ICP Scoring Framework

### 8 Dimensions

| Dimension | Description | Weight | Max Score |
|-----------|-------------|--------|-----------|
| **Venue Type** | Type of institution and athletic program level | 3 | 10 |
| **Geography** | Location within target territory | 2 | 10 |
| **Budget Signals** | Evidence of capital availability | 3 | 10 |
| **Current Lighting Age** | Age and type of existing lighting | 2 | 10 |
| **Night Game Frequency** | How often venue is used for night events | 2 | 10 |
| **Broadcast Requirements** | TV/streaming lighting needs | 2 | 10 |
| **Decision Maker Access** | Quality of contact/relationship | 2 | 10 |
| **Project Timeline** | Urgency and clarity of timeline | 3 | 10 |

**Total Weight:** 19  
**Max Raw Score:** 190  
**Normalized to:** 0-100

### Scoring Rubrics

#### 1. Venue Type (Weight: 3)

```python
VENUE_TYPE_SCORES = {
    'college_d1': 10,      # Large stadiums, big budgets, high visibility
    'college_d2': 8,       # Solid programs, good budgets
    'high_school_6a': 8,   # Largest high schools, often comparable to small colleges
    'high_school_5a': 7,   # Large high schools, competitive programs
    'college_d3': 6,       # Smaller budgets but can still be good fits
    'college_naia': 6,     # Similar to D3
    'high_school_4a': 5,   # Mid-size, may have budget constraints
    'high_school_3a': 3,   # Smaller, likely budget constrained
    'high_school_other': 2, # Small schools, rarely a fit
}
```

#### 2. Geography (Weight: 2)

```python
def score_geography(state: str, city: str = None) -> int:
    """
    Score based on location within target territory.
    
    Primary states (home territory): 10
    Adjacent states (reachable): 6
    Outside territory: 2
    """
    PRIMARY_STATES = {'OH', 'IN', 'PA', 'KY', 'IL'}
    ADJACENT_STATES = {'MI', 'WV', 'TN', 'MO', 'WI'}
    
    if state in PRIMARY_STATES:
        return 10
    elif state in ADJACENT_STATES:
        return 6
    else:
        return 2
```

#### 3. Budget Signals (Weight: 3)

```python
def score_budget_signals(prospect: Prospect) -> tuple[int, str]:
    """
    Score based on evidence of capital availability.
    
    Returns: (score, rationale)
    """
    score = 3  # Default: unknown
    signals = []
    
    # Check for known signals (stored in prospect or from research)
    if prospect.has_recent_bond_measure:
        score = 10
        signals.append("Bond measure passed in last 24 months")
    elif prospect.has_capital_campaign:
        score = 9
        signals.append("Active capital campaign")
    elif prospect.venue_type.startswith('college_d1'):
        score = 8  # D1 programs typically have budgets
        signals.append("D1 program (typically well-funded)")
    elif prospect.has_facility_master_plan:
        score = 7
        signals.append("Facility master plan includes lighting")
    elif prospect.enrollment and prospect.enrollment > 2500:
        score = 5  # Larger schools more likely to have funds
        signals.append("Large enrollment suggests adequate funding")
    
    return score, "; ".join(signals) if signals else "No budget signals detected"
```

#### 4. Current Lighting Age (Weight: 2)

```python
def score_lighting_age(lighting_type: str, age_years: int = None) -> tuple[int, str]:
    """
    Score based on current lighting situation.
    
    Older/worse lighting = higher score (more need).
    """
    if lighting_type == 'metal_halide':
        if age_years and age_years >= 15:
            return 10, f"Metal halide fixtures {age_years}+ years old - prime for replacement"
        elif age_years and age_years >= 10:
            return 8, f"Metal halide fixtures {age_years} years old - nearing end of life"
        else:
            return 7, "Metal halide fixtures - LED upgrade candidate"
    
    elif lighting_type == 'early_led':
        if age_years and age_years >= 8:
            return 7, f"Early-gen LED {age_years}+ years old - may lack features"
        else:
            return 4, "LED lighting installed relatively recently"
    
    elif lighting_type == 'modern_led':
        return 2, "Modern LED lighting - unlikely to need upgrade"
    
    else:  # unknown
        return 5, "Lighting type unknown - needs research"
```

#### 5. Night Game Frequency (Weight: 2)

```python
def score_night_games(has_night_games: bool, night_game_count: int = None) -> tuple[int, str]:
    """
    Score based on night event frequency.
    
    More night games = more value from lighting investment.
    """
    if not has_night_games:
        return 2, "No night games - limited lighting ROI"
    
    if night_game_count:
        if night_game_count >= 20:
            return 10, f"{night_game_count} night events/year - heavy usage"
        elif night_game_count >= 10:
            return 8, f"{night_game_count} night events/year - regular usage"
        elif night_game_count >= 5:
            return 6, f"{night_game_count} night events/year - moderate usage"
        else:
            return 4, f"{night_game_count} night events/year - light usage"
    
    # Unknown count but has night games
    return 6, "Night games confirmed - frequency unknown"
```

#### 6. Broadcast Requirements (Weight: 2)

```python
def score_broadcast(broadcast_requirements: str) -> tuple[int, str]:
    """
    Score based on TV/streaming lighting needs.
    
    Broadcast requirements often mandate specific lighting levels.
    """
    BROADCAST_SCORES = {
        'espn': (10, "ESPN/major network broadcasts - strict lighting requirements"),
        'conference_network': (8, "Conference network broadcasts - professional standards needed"),
        'local_streaming': (5, "Local streaming - basic HD lighting adequate"),
        'none': (3, "No broadcast requirements"),
    }
    
    return BROADCAST_SCORES.get(broadcast_requirements, (4, "Broadcast requirements unknown"))
```

#### 7. Decision Maker Access (Weight: 2)

```python
def score_decision_maker_access(prospect: Prospect, contacts: List[Contact]) -> tuple[int, str]:
    """
    Score based on quality of decision maker contact.
    """
    if not contacts:
        return 3, "No contacts identified"
    
    primary_contact = next((c for c in contacts if c.is_primary), None)
    
    if not primary_contact:
        return 4, f"Contacts identified but no primary: {len(contacts)} total"
    
    # Score based on title and engagement
    if primary_contact.title and 'athletic director' in primary_contact.title.lower():
        if primary_contact.last_response_at:
            return 10, f"Athletic Director engaged - responded {primary_contact.last_response_at}"
        elif primary_contact.email:
            return 7, "Athletic Director contact with email"
        else:
            return 5, "Athletic Director identified but no email"
    
    elif primary_contact.title and 'facilities' in primary_contact.title.lower():
        if primary_contact.email:
            return 6, "Facilities Director contact with email"
        else:
            return 4, "Facilities Director identified but no email"
    
    return 4, f"Contact identified: {primary_contact.title or 'Unknown title'}"
```

#### 8. Project Timeline (Weight: 3)

```python
def score_project_timeline(timeline: str, has_active_rfp: bool = False) -> tuple[int, str]:
    """
    Score based on project urgency and clarity.
    """
    if has_active_rfp:
        return 10, "Active RFP - immediate opportunity"
    
    TIMELINE_SCORES = {
        'immediate': (10, "Immediate project - actively seeking quotes"),
        'within_6_months': (8, "Project planned within 6 months"),
        'within_12_months': (6, "Project planned within 12 months"),
        '12_plus_months': (4, "Project 12+ months out"),
        'unknown': (3, "Timeline unknown"),
    }
    
    return TIMELINE_SCORES.get(timeline, (3, "Timeline unknown"))
```

### Score Calculation

```python
def calculate_icp_score(prospect: Prospect, contacts: List[Contact]) -> ICPScoreResult:
    """
    Calculate total ICP score across all dimensions.
    
    Returns normalized score (0-100) and tier assignment.
    """
    dimensions = {}
    
    # Score each dimension
    dimensions['venue_type'] = (VENUE_TYPE_SCORES.get(prospect.venue_type, 3), 3)
    dimensions['geography'] = (score_geography(prospect.state), 2)
    dimensions['budget_signals'] = (score_budget_signals(prospect)[0], 3)
    dimensions['current_lighting_age'] = (score_lighting_age(prospect.current_lighting_type, prospect.current_lighting_age_years)[0], 2)
    dimensions['night_game_frequency'] = (score_night_games(prospect.has_night_games)[0], 2)
    dimensions['broadcast_requirements'] = (score_broadcast(prospect.broadcast_requirements)[0], 2)
    dimensions['decision_maker_access'] = (score_decision_maker_access(prospect, contacts)[0], 2)
    dimensions['project_timeline'] = (score_project_timeline(prospect.estimated_project_timeline)[0], 3)
    
    # Calculate weighted score
    raw_score = sum(score * weight for score, weight in dimensions.values())
    max_possible = sum(10 * weight for _, weight in dimensions.values())  # 190
    
    normalized_score = int((raw_score / max_possible) * 100)
    
    # Assign tier
    tier = assign_tier(normalized_score)
    
    return ICPScoreResult(
        total_score=normalized_score,
        tier=tier,
        dimensions=dimensions,
    )

def assign_tier(score: int) -> str:
    """Assign tier based on normalized score."""
    if score >= 70:
        return 'A1'
    elif score >= 55:
        return 'A2'
    elif score >= 40:
        return 'B'
    elif score >= 25:
        return 'C'
    else:
        return 'D'
```

---

## Agent Implementation

### File Structure

```
agents/hygiene/
├── __init__.py
├── agent.py              # Main HygieneAgent class
├── scoring.py            # ICPScorer class
├── quality_checks.py     # Data quality validation
├── staleness.py          # Staleness detection
└── config.py             # Scoring configuration
```

### Main Agent Class

```python
# agents/hygiene/agent.py

from agents.base import BaseAgent
from agents.hygiene.scoring import ICPScorer
from agents.hygiene.quality_checks import QualityChecker
from agents.hygiene.staleness import StalenessDetector
from database.models import Prospect, Contact, ProspectScore, HygieneFlag
from typing import List
import logging

logger = logging.getLogger(__name__)

class HygieneAgent(BaseAgent):
    """
    Agent that scores prospects and maintains data quality.
    
    Run modes:
    - new_prospects: Score all prospects in 'identified' or 'needs_scoring' status
    - rescore: Rescore all prospects (e.g., after scoring logic changes)
    - quality_check: Run data quality checks without rescoring
    - staleness: Check for stale prospects
    """
    
    name = "hygiene"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.scorer = ICPScorer()
        self.quality_checker = QualityChecker(db_session)
        self.staleness_detector = StalenessDetector(db_session)
    
    def run_cycle(self, mode: str = 'new_prospects') -> dict:
        """
        Run a hygiene cycle.
        
        Args:
            mode: 'new_prospects', 'rescore', 'quality_check', 'staleness'
        
        Returns:
            Summary of results
        """
        results = {
            'scored': 0,
            'tier_changes': [],
            'flags_created': 0,
            'errors': [],
        }
        
        if mode in ('new_prospects', 'rescore'):
            results.update(self._score_prospects(mode))
        
        if mode in ('new_prospects', 'quality_check'):
            results['flags_created'] = self._run_quality_checks()
        
        if mode in ('staleness',):
            results['stale_detected'] = self._detect_staleness()
        
        return results
    
    def _score_prospects(self, mode: str) -> dict:
        """Score prospects and assign tiers."""
        if mode == 'new_prospects':
            prospects = self.db.query(Prospect).filter(
                Prospect.status.in_(['identified', 'needs_scoring']),
                Prospect.deleted_at.is_(None)
            ).all()
        else:  # rescore all
            prospects = self.db.query(Prospect).filter(
                Prospect.deleted_at.is_(None)
            ).all()
        
        scored = 0
        tier_changes = []
        
        for prospect in prospects:
            try:
                old_tier = prospect.tier
                old_score = prospect.icp_score
                
                # Get contacts for this prospect
                contacts = self.db.query(Contact).filter(
                    Contact.prospect_id == prospect.id,
                    Contact.deleted_at.is_(None)
                ).all()
                
                # Calculate score
                result = self.scorer.calculate(prospect, contacts)
                
                # Update prospect
                prospect.icp_score = result.total_score
                prospect.tier = result.tier
                
                # Update status
                if prospect.status == 'identified':
                    prospect.status = 'needs_scoring'
                if prospect.status == 'needs_scoring':
                    prospect.status = 'scored'
                
                # Move to appropriate next state based on tier
                if result.tier in ('A1', 'A2') and prospect.status == 'scored':
                    prospect.status = 'needs_research'
                elif result.tier in ('C', 'D') and prospect.status == 'scored':
                    prospect.status = 'deprioritized'
                
                # Save dimension scores
                self._save_dimension_scores(prospect.id, result)
                
                self.db.commit()
                scored += 1
                
                # Track tier changes
                if old_tier and old_tier != result.tier:
                    tier_changes.append({
                        'prospect_id': prospect.id,
                        'name': prospect.name,
                        'old_tier': old_tier,
                        'new_tier': result.tier,
                        'old_score': old_score,
                        'new_score': result.total_score,
                    })
                
                self.log_action(
                    action="prospect_scored",
                    prospect_id=prospect.id,
                    details={
                        "score": result.total_score,
                        "tier": result.tier,
                        "old_tier": old_tier,
                    }
                )
                
            except Exception as e:
                logger.error(f"Error scoring prospect {prospect.id}: {e}")
        
        return {'scored': scored, 'tier_changes': tier_changes}
    
    def _save_dimension_scores(self, prospect_id: str, result) -> None:
        """Save individual dimension scores for audit trail."""
        for dimension, (score, weight) in result.dimensions.items():
            score_record = ProspectScore(
                prospect_id=prospect_id,
                dimension=dimension,
                score=score,
                weight=weight,
                notes=result.dimension_notes.get(dimension, ''),
                scored_by=f"agent:{self.name}",
            )
            self.db.add(score_record)
    
    def _run_quality_checks(self) -> int:
        """Run data quality checks and create flags."""
        return self.quality_checker.run_all_checks()
    
    def _detect_staleness(self) -> int:
        """Detect and flag stale prospects."""
        return self.staleness_detector.detect()
```

### Quality Checker

```python
# agents/hygiene/quality_checks.py

from database.models import Prospect, Contact, HygieneFlag
from datetime import datetime, timedelta

class QualityChecker:
    """Run data quality checks and create hygiene flags."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def run_all_checks(self) -> int:
        """Run all quality checks. Returns count of flags created."""
        flags_created = 0
        
        flags_created += self._check_missing_contacts()
        flags_created += self._check_missing_emails()
        flags_created += self._check_incomplete_data()
        flags_created += self._check_duplicate_suspects()
        
        return flags_created
    
    def _check_missing_contacts(self) -> int:
        """Flag A1/A2 prospects without any contacts."""
        prospects = self.db.query(Prospect).filter(
            Prospect.tier.in_(['A1', 'A2']),
            Prospect.deleted_at.is_(None)
        ).all()
        
        flags_created = 0
        
        for prospect in prospects:
            contacts = self.db.query(Contact).filter(
                Contact.prospect_id == prospect.id,
                Contact.deleted_at.is_(None)
            ).count()
            
            if contacts == 0:
                if self._create_flag(
                    prospect_id=prospect.id,
                    flag_type='missing_contact',
                    severity='warning',
                    message=f"High-priority prospect ({prospect.tier}) has no contacts",
                    suggested_action="Find Athletic Director or Facilities Director contact"
                ):
                    flags_created += 1
        
        return flags_created
    
    def _check_missing_emails(self) -> int:
        """Flag A1/A2 prospects where primary contact has no email."""
        contacts = self.db.query(Contact).join(Prospect).filter(
            Prospect.tier.in_(['A1', 'A2']),
            Contact.is_primary == True,
            Contact.email.is_(None),
            Contact.deleted_at.is_(None),
            Prospect.deleted_at.is_(None)
        ).all()
        
        flags_created = 0
        
        for contact in contacts:
            if self._create_flag(
                prospect_id=contact.prospect_id,
                flag_type='missing_email',
                severity='warning',
                message=f"Primary contact {contact.name} has no email address",
                suggested_action="Find email via Hunter.io or LinkedIn"
            ):
                flags_created += 1
        
        return flags_created
    
    def _check_incomplete_data(self) -> int:
        """Flag prospects missing key data fields."""
        prospects = self.db.query(Prospect).filter(
            Prospect.tier.in_(['A1', 'A2', 'B']),
            Prospect.deleted_at.is_(None)
        ).all()
        
        flags_created = 0
        
        for prospect in prospects:
            missing = []
            
            if not prospect.stadium_name:
                missing.append('stadium_name')
            if not prospect.current_lighting_type:
                missing.append('current_lighting_type')
            if not prospect.primary_sport:
                missing.append('primary_sport')
            
            if missing:
                if self._create_flag(
                    prospect_id=prospect.id,
                    flag_type='data_quality',
                    severity='info',
                    message=f"Missing data fields: {', '.join(missing)}",
                    suggested_action="Research and complete missing fields"
                ):
                    flags_created += 1
        
        return flags_created
    
    def _check_duplicate_suspects(self) -> int:
        """Flag potential duplicate prospects."""
        # Implementation: Find prospects with very similar names
        # This is a safety net for deduplication misses
        return 0  # TODO: Implement
    
    def _create_flag(self, prospect_id: str, flag_type: str, severity: str, 
                     message: str, suggested_action: str) -> bool:
        """Create a hygiene flag if one doesn't already exist."""
        existing = self.db.query(HygieneFlag).filter(
            HygieneFlag.prospect_id == prospect_id,
            HygieneFlag.flag_type == flag_type,
            HygieneFlag.resolved_at.is_(None)
        ).first()
        
        if existing:
            return False
        
        flag = HygieneFlag(
            prospect_id=prospect_id,
            flag_type=flag_type,
            severity=severity,
            message=message,
            suggested_action=suggested_action,
        )
        self.db.add(flag)
        self.db.commit()
        
        return True
```

---

## API Endpoints

```python
# api/routes/hygiene.py

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/api/v1/hygiene", tags=["hygiene"])

@router.post("/run")
async def run_hygiene(
    background_tasks: BackgroundTasks,
    mode: str = 'new_prospects'
):
    """
    Trigger a hygiene run.
    
    Modes:
    - new_prospects: Score unscored prospects
    - rescore: Rescore all prospects
    - quality_check: Run quality checks only
    - staleness: Check for stale prospects
    """
    background_tasks.add_task(run_hygiene_task, mode)
    return {"status": "started", "mode": mode}

@router.post("/score/{prospect_id}")
async def score_prospect(prospect_id: str):
    """Score or rescore a single prospect."""
    pass

@router.get("/flags")
async def list_flags(
    resolved: bool = False,
    severity: str = None,
    limit: int = 50
):
    """List hygiene flags."""
    pass

@router.post("/flags/{flag_id}/resolve")
async def resolve_flag(flag_id: str, resolution_notes: str = None):
    """Mark a flag as resolved."""
    pass
```

---

## Testing

### Test Cases

1. **Scoring Calculation**
   - Each dimension scores correctly
   - Weights apply correctly
   - Normalization produces 0-100 range
   - Tier thresholds work correctly

2. **Tier Assignment**
   - Score 70+ → A1
   - Score 55-69 → A2
   - Score 40-54 → B
   - Score 25-39 → C
   - Score <25 → D

3. **State Transitions**
   - identified → scored → needs_research (A1/A2)
   - identified → scored → deprioritized (C/D)
   - B tier stays in scored for manual review

4. **Quality Checks**
   - Missing contact flagged for A1/A2
   - Missing email flagged for primary contact
   - Flags not duplicated if already exists

---

## Related Documents

- [Database Schema](01-database-schema.md) - ProspectScore and HygieneFlag tables
- [Prospector Agent](02-prospector-agent.md) - Creates prospects to be scored
- [Researcher Agent](04-researcher-agent.md) - Runs after scoring for A1/A2
- [Orchestrator Agent](06-orchestrator-agent.md) - Triggers Researcher after Hygiene
