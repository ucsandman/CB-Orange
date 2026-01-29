# Orchestrator Agent Build Specification

**Version:** 1.0  
**Created:** 2026-01-29  
**Purpose:** Specification for the meta-agent that coordinates all other agents

---

## Overview

The Orchestrator Agent is a meta-agent that monitors the health of other agents, coordinates handoffs between pipeline stages, and generates operational reports. Unlike other agents, it does not modify prospect data directly.

### Responsibilities

1. **Health Monitoring** - Detect agent failures, stalls, and anomalies
2. **Handoff Coordination** - Trigger the next agent when the previous completes
3. **State Validation** - Ensure prospects flow through states correctly
4. **Conflict Resolution** - Arbitrate when multiple agents want the same record
5. **Reporting** - Generate daily/weekly pipeline health summaries

### Non-Responsibilities

- Directly modifying prospect or deal data
- Running the actual prospecting, scoring, research, or outreach logic

---

## Monitoring Dimensions

### Agent Health

```python
@dataclass
class AgentHealth:
    """Health status for a single agent."""
    agent_name: str
    status: str                    # healthy, degraded, failing, unknown
    last_successful_run: datetime
    last_run_duration_seconds: float
    runs_last_24h: int
    errors_last_24h: int
    error_rate: float              # errors / runs
    avg_records_per_run: float
    
    @property
    def is_healthy(self) -> bool:
        return (
            self.status == 'healthy' and
            self.error_rate < 0.1 and
            self.last_successful_run > datetime.utcnow() - timedelta(hours=6)
        )
```

### Health Thresholds

| Metric | Healthy | Degraded | Failing |
|--------|---------|----------|---------|
| Error rate | < 10% | 10-30% | > 30% |
| Time since last success | < 6 hours | 6-24 hours | > 24 hours |
| Records per run | > expected * 0.5 | > expected * 0.2 | < expected * 0.2 |

### Pipeline Flow

```
Prospector ──▶ Hygiene ──▶ Researcher ──▶ Outreach
    │             │             │            │
    └─────────────┴─────────────┴────────────┘
                       │
                 Orchestrator
              (monitors all, owns none)
```

---

## Handoff Logic

### State Transition Triggers

```python
HANDOFF_TRIGGERS = {
    'identified': {
        'next_agent': 'hygiene',
        'trigger': 'immediate',  # Run hygiene as soon as prospect is created
    },
    'needs_scoring': {
        'next_agent': 'hygiene',
        'trigger': 'immediate',
    },
    'scored': {
        'next_agent': 'researcher',
        'condition': lambda p: p.tier in ('A1', 'A2'),  # Only research high-priority
        'trigger': 'immediate',
    },
    'needs_research': {
        'next_agent': 'researcher',
        'trigger': 'immediate',
    },
    'research_complete': {
        'next_agent': 'outreach',
        'condition': lambda p: p.tier in ('A1', 'A2', 'B') and has_contact_with_email(p),
        'trigger': 'immediate',
    },
    'ready_for_outreach': {
        'next_agent': 'outreach',
        'trigger': 'immediate',
    },
}
```

### Handoff Execution

```python
class HandoffManager:
    """Manage handoffs between agents."""
    
    def check_pending_handoffs(self) -> List[Handoff]:
        """Find prospects that need to move to the next agent."""
        pending = []
        
        for state, config in HANDOFF_TRIGGERS.items():
            prospects = self.db.query(Prospect).filter(
                Prospect.status == state,
                Prospect.deleted_at.is_(None)
            ).all()
            
            for prospect in prospects:
                # Check condition if exists
                if 'condition' in config:
                    if not config['condition'](prospect):
                        continue
                
                pending.append(Handoff(
                    prospect_id=prospect.id,
                    from_state=state,
                    to_agent=config['next_agent'],
                ))
        
        return pending
    
    def execute_handoff(self, handoff: Handoff) -> bool:
        """Trigger the appropriate agent for a handoff."""
        agent_runners = {
            'hygiene': self._trigger_hygiene,
            'researcher': self._trigger_researcher,
            'outreach': self._trigger_outreach,
        }
        
        runner = agent_runners.get(handoff.to_agent)
        if runner:
            return runner(handoff.prospect_id)
        return False
```

---

## Agent Implementation

### File Structure

```
agents/orchestrator/
├── __init__.py
├── agent.py              # Main OrchestratorAgent class
├── health_monitor.py     # Health checking logic
├── handoff_manager.py    # Handoff coordination
├── conflict_resolver.py  # Lock conflict resolution
├── reporter.py           # Pipeline reports
└── config.py
```

### Main Agent Class

```python
# agents/orchestrator/agent.py

from agents.base import BaseAgent
from agents.orchestrator.health_monitor import HealthMonitor
from agents.orchestrator.handoff_manager import HandoffManager
from agents.orchestrator.conflict_resolver import ConflictResolver
from agents.orchestrator.reporter import PipelineReporter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """
    Meta-agent that coordinates all other agents.
    
    Does not modify prospect data directly - only observes and coordinates.
    
    Run modes:
    - monitor: Check agent health and alert if issues
    - handoffs: Process pending handoffs
    - resolve: Resolve any lock conflicts
    - report: Generate pipeline report
    - full: All of the above
    """
    
    name = "orchestrator"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.health_monitor = HealthMonitor(db_session)
        self.handoff_manager = HandoffManager(db_session)
        self.conflict_resolver = ConflictResolver(db_session)
        self.reporter = PipelineReporter(db_session)
    
    def run_cycle(self, mode: str = 'full') -> dict:
        """
        Run an orchestration cycle.
        
        Args:
            mode: 'monitor', 'handoffs', 'resolve', 'report', 'full'
        
        Returns:
            Summary of actions taken
        """
        results = {}
        
        if mode in ('monitor', 'full'):
            results['health'] = self._check_health()
        
        if mode in ('handoffs', 'full'):
            results['handoffs'] = self._process_handoffs()
        
        if mode in ('resolve', 'full'):
            results['conflicts'] = self._resolve_conflicts()
        
        if mode in ('report', 'full'):
            results['report'] = self._generate_report()
        
        return results
    
    def _check_health(self) -> dict:
        """Check health of all agents."""
        health_status = self.health_monitor.check_all_agents()
        
        alerts = []
        for agent_name, health in health_status.items():
            if not health.is_healthy:
                alert = self._create_alert(agent_name, health)
                alerts.append(alert)
                
                self.emit_event("agent_unhealthy", {
                    "agent": agent_name,
                    "status": health.status,
                    "error_rate": health.error_rate,
                })
        
        return {
            'agents_checked': len(health_status),
            'healthy': sum(1 for h in health_status.values() if h.is_healthy),
            'alerts_created': len(alerts),
        }
    
    def _process_handoffs(self) -> dict:
        """Process pending handoffs between agents."""
        pending = self.handoff_manager.check_pending_handoffs()
        
        executed = 0
        failed = 0
        
        for handoff in pending:
            try:
                success = self.handoff_manager.execute_handoff(handoff)
                if success:
                    executed += 1
                    self.log_action(
                        action="handoff_executed",
                        prospect_id=handoff.prospect_id,
                        details={
                            "from_state": handoff.from_state,
                            "to_agent": handoff.to_agent,
                        }
                    )
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Handoff failed: {e}")
                failed += 1
        
        return {
            'pending': len(pending),
            'executed': executed,
            'failed': failed,
        }
    
    def _resolve_conflicts(self) -> dict:
        """Resolve any lock conflicts."""
        conflicts = self.conflict_resolver.find_conflicts()
        
        resolved = 0
        for conflict in conflicts:
            if self.conflict_resolver.resolve(conflict):
                resolved += 1
        
        return {
            'conflicts_found': len(conflicts),
            'resolved': resolved,
        }
    
    def _generate_report(self) -> dict:
        """Generate pipeline health report."""
        report = self.reporter.generate_daily_report()
        
        # Store report
        self._save_report(report)
        
        # Emit event for dashboard
        self.emit_event("report_generated", {
            "date": report.date.isoformat(),
            "summary": report.summary,
        })
        
        return report.to_dict()
    
    def _create_alert(self, agent_name: str, health: AgentHealth) -> dict:
        """Create an alert for an unhealthy agent."""
        alert = {
            'type': 'agent_health',
            'agent': agent_name,
            'status': health.status,
            'message': f"{agent_name} is {health.status}: {health.error_rate:.0%} error rate",
            'created_at': datetime.utcnow(),
        }
        
        # TODO: Send to notification system
        
        return alert
```

### Health Monitor

```python
# agents/orchestrator/health_monitor.py

from database.models import AgentRun
from datetime import datetime, timedelta
from typing import Dict

class HealthMonitor:
    """Monitor health of all agents."""
    
    EXPECTED_RECORDS_PER_RUN = {
        'prospector': 10,  # Expect ~10 new prospects per run
        'hygiene': 20,     # Expect ~20 scored per run
        'researcher': 5,   # Expect ~5 researched per run
        'outreach': 10,    # Expect ~10 emails per run
    }
    
    def __init__(self, db_session):
        self.db = db_session
    
    def check_all_agents(self) -> Dict[str, AgentHealth]:
        """Check health of all agents."""
        agents = ['prospector', 'hygiene', 'researcher', 'outreach']
        return {agent: self.check_agent(agent) for agent in agents}
    
    def check_agent(self, agent_name: str) -> AgentHealth:
        """Check health of a single agent."""
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        
        # Get runs from last 24 hours
        runs = self.db.query(AgentRun).filter(
            AgentRun.agent_name == agent_name,
            AgentRun.started_at >= yesterday
        ).all()
        
        if not runs:
            return AgentHealth(
                agent_name=agent_name,
                status='unknown',
                last_successful_run=None,
                last_run_duration_seconds=0,
                runs_last_24h=0,
                errors_last_24h=0,
                error_rate=0,
                avg_records_per_run=0,
            )
        
        # Calculate metrics
        successful_runs = [r for r in runs if r.status == 'completed']
        failed_runs = [r for r in runs if r.status == 'failed']
        
        last_success = max(
            (r.completed_at for r in successful_runs if r.completed_at),
            default=None
        )
        
        error_rate = len(failed_runs) / len(runs) if runs else 0
        
        avg_records = sum(r.records_processed or 0 for r in successful_runs) / len(successful_runs) if successful_runs else 0
        
        # Determine status
        status = self._determine_status(
            error_rate=error_rate,
            last_success=last_success,
            avg_records=avg_records,
            expected_records=self.EXPECTED_RECORDS_PER_RUN.get(agent_name, 10),
        )
        
        return AgentHealth(
            agent_name=agent_name,
            status=status,
            last_successful_run=last_success,
            last_run_duration_seconds=self._avg_duration(successful_runs),
            runs_last_24h=len(runs),
            errors_last_24h=len(failed_runs),
            error_rate=error_rate,
            avg_records_per_run=avg_records,
        )
    
    def _determine_status(self, error_rate: float, last_success: datetime,
                          avg_records: float, expected_records: float) -> str:
        """Determine agent status based on metrics."""
        now = datetime.utcnow()
        
        # Check for failures
        if error_rate > 0.3:
            return 'failing'
        
        if last_success and (now - last_success) > timedelta(hours=24):
            return 'failing'
        
        # Check for degradation
        if error_rate > 0.1:
            return 'degraded'
        
        if last_success and (now - last_success) > timedelta(hours=6):
            return 'degraded'
        
        if avg_records < expected_records * 0.2:
            return 'degraded'
        
        return 'healthy'
    
    def _avg_duration(self, runs: list) -> float:
        """Calculate average run duration."""
        durations = [
            (r.completed_at - r.started_at).total_seconds()
            for r in runs
            if r.completed_at and r.started_at
        ]
        return sum(durations) / len(durations) if durations else 0
```

### Pipeline Reporter

```python
# agents/orchestrator/reporter.py

from database.models import Prospect, Activity, OutreachSequence, AgentRun
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PipelineReport:
    """Daily pipeline health report."""
    date: datetime
    
    # Pipeline counts
    total_prospects: int
    prospects_by_status: Dict[str, int]
    prospects_by_tier: Dict[str, int]
    
    # Activity metrics
    prospects_added_24h: int
    prospects_scored_24h: int
    prospects_researched_24h: int
    emails_sent_24h: int
    
    # Sequence metrics
    active_sequences: int
    sequences_completed_24h: int
    response_rate: float
    
    # Agent metrics
    agent_runs_24h: int
    agent_errors_24h: int
    
    # Summary
    summary: str
    
    def to_dict(self) -> dict:
        return {
            'date': self.date.isoformat(),
            'total_prospects': self.total_prospects,
            'prospects_by_status': self.prospects_by_status,
            'prospects_by_tier': self.prospects_by_tier,
            'activity': {
                'added': self.prospects_added_24h,
                'scored': self.prospects_scored_24h,
                'researched': self.prospects_researched_24h,
                'emails_sent': self.emails_sent_24h,
            },
            'sequences': {
                'active': self.active_sequences,
                'completed': self.sequences_completed_24h,
                'response_rate': self.response_rate,
            },
            'agents': {
                'runs': self.agent_runs_24h,
                'errors': self.agent_errors_24h,
            },
            'summary': self.summary,
        }

class PipelineReporter:
    """Generate pipeline reports."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_daily_report(self) -> PipelineReport:
        """Generate a daily pipeline report."""
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        
        # Pipeline counts
        prospects = self.db.query(Prospect).filter(
            Prospect.deleted_at.is_(None)
        ).all()
        
        by_status = {}
        by_tier = {}
        for p in prospects:
            by_status[p.status] = by_status.get(p.status, 0) + 1
            if p.tier:
                by_tier[p.tier] = by_tier.get(p.tier, 0) + 1
        
        # Activity metrics
        added = self.db.query(Prospect).filter(
            Prospect.created_at >= yesterday
        ).count()
        
        scored = self.db.query(Activity).filter(
            Activity.type == 'score_change',
            Activity.created_at >= yesterday
        ).count()
        
        researched = self.db.query(Activity).filter(
            Activity.type == 'research_completed',
            Activity.created_at >= yesterday
        ).count()
        
        emails = self.db.query(Activity).filter(
            Activity.type == 'email_sent',
            Activity.created_at >= yesterday
        ).count()
        
        # Sequence metrics
        active_seqs = self.db.query(OutreachSequence).filter(
            OutreachSequence.status == 'active'
        ).count()
        
        completed_seqs = self.db.query(OutreachSequence).filter(
            OutreachSequence.completed_at >= yesterday
        ).count()
        
        # Response rate (replies / emails sent last 7 days)
        week_ago = now - timedelta(days=7)
        emails_week = self.db.query(Activity).filter(
            Activity.type == 'email_sent',
            Activity.created_at >= week_ago
        ).count()
        
        replies_week = self.db.query(Activity).filter(
            Activity.type == 'email_received',
            Activity.created_at >= week_ago
        ).count()
        
        response_rate = replies_week / emails_week if emails_week > 0 else 0
        
        # Agent metrics
        runs = self.db.query(AgentRun).filter(
            AgentRun.started_at >= yesterday
        ).all()
        
        errors = sum(1 for r in runs if r.status == 'failed')
        
        # Generate summary
        summary = self._generate_summary(
            total=len(prospects),
            added=added,
            by_tier=by_tier,
            emails=emails,
            response_rate=response_rate,
        )
        
        return PipelineReport(
            date=now,
            total_prospects=len(prospects),
            prospects_by_status=by_status,
            prospects_by_tier=by_tier,
            prospects_added_24h=added,
            prospects_scored_24h=scored,
            prospects_researched_24h=researched,
            emails_sent_24h=emails,
            active_sequences=active_seqs,
            sequences_completed_24h=completed_seqs,
            response_rate=response_rate,
            agent_runs_24h=len(runs),
            agent_errors_24h=errors,
            summary=summary,
        )
    
    def _generate_summary(self, total: int, added: int, by_tier: dict,
                          emails: int, response_rate: float) -> str:
        """Generate human-readable summary."""
        a1_count = by_tier.get('A1', 0)
        a2_count = by_tier.get('A2', 0)
        
        parts = [
            f"Pipeline has {total} total prospects",
            f"({a1_count} A1, {a2_count} A2).",
            f"Added {added} new prospects today.",
            f"Sent {emails} emails.",
        ]
        
        if response_rate > 0.15:
            parts.append(f"Response rate is strong at {response_rate:.0%}.")
        elif response_rate > 0.05:
            parts.append(f"Response rate is {response_rate:.0%}.")
        elif emails > 0:
            parts.append(f"Response rate is low at {response_rate:.0%}.")
        
        return " ".join(parts)
```

---

## Scheduling

The Orchestrator runs more frequently than other agents to ensure smooth pipeline flow:

```python
ORCHESTRATOR_SCHEDULE = {
    'health_check': '*/15 * * * *',    # Every 15 minutes
    'handoffs': '*/5 * * * *',         # Every 5 minutes
    'conflict_resolution': '*/30 * * * *',  # Every 30 minutes
    'daily_report': '0 8 * * *',       # Daily at 8 AM
}
```

---

## API Endpoints

```python
# api/routes/orchestrator.py

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])

@router.get("/health")
async def get_health():
    """Get health status of all agents."""
    pass

@router.get("/report/today")
async def get_today_report():
    """Get today's pipeline report."""
    pass

@router.get("/report/{date}")
async def get_report(date: str):
    """Get pipeline report for a specific date."""
    pass

@router.post("/run")
async def run_orchestrator(mode: str = 'full'):
    """Manually trigger orchestrator run."""
    pass
```

---

## Related Documents

- [Database Schema](01-database-schema.md) - AgentRun and audit tables
- [Prospector Agent](02-prospector-agent.md) - First agent in pipeline
- [Hygiene Agent](03-hygiene-agent.md) - Scoring agent
- [Researcher Agent](04-researcher-agent.md) - Research agent
- [Outreach Agent](05-outreach-agent.md) - Final agent in pipeline
- [Dashboard](07-dashboard.md) - Displays health and reports
