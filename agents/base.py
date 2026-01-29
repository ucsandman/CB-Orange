"""Base agent class for all pipeline agents."""
import json
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

from database.models import AgentRun, AgentAuditLog


class BaseAgent(ABC):
    """Base class for all pipeline agents.

    All agents (Prospector, Hygiene, Researcher, Outreach, Orchestrator)
    should extend this class to ensure consistent behavior.
    """

    def __init__(self, db: Session, agent_name: str):
        self.db = db
        self.agent_name = agent_name
        self.run: Optional[AgentRun] = None
        self.records_processed = 0
        self.records_created = 0
        self.records_updated = 0

    def start_run(self, trigger: str = "scheduled") -> AgentRun:
        """Start a new agent run and create the tracking record."""
        self.run = AgentRun(
            agent_name=self.agent_name,
            trigger=trigger,
            status="running",
        )
        self.db.add(self.run)
        self.db.commit()
        self.db.refresh(self.run)
        return self.run

    def complete_run(self):
        """Mark the current run as completed successfully."""
        if self.run:
            self.run.status = "completed"
            self.run.completed_at = datetime.utcnow()
            self.run.records_processed = self.records_processed
            self.run.records_created = self.records_created
            self.run.records_updated = self.records_updated
            self.db.commit()

    def fail_run(self, error: Exception):
        """Mark the current run as failed with error details."""
        if self.run:
            self.run.status = "failed"
            self.run.completed_at = datetime.utcnow()
            self.run.error_message = str(error)
            self.run.error_traceback = traceback.format_exc()
            self.run.records_processed = self.records_processed
            self.run.records_created = self.records_created
            self.run.records_updated = self.records_updated
            self.db.commit()

    def log_action(
        self,
        action: str,
        prospect_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        details: Optional[dict] = None,
        requires_review: bool = False,
    ) -> AgentAuditLog:
        """Log an agent action to the audit log.

        Args:
            action: The action being performed (e.g., 'prospect_created', 'email_drafted')
            prospect_id: Optional ID of the prospect being acted upon
            contact_id: Optional ID of the contact being acted upon
            details: Optional dict with action-specific data
            requires_review: Whether this action requires human review

        Returns:
            The created AgentAuditLog record
        """
        audit_log = AgentAuditLog(
            agent_run_id=self.run.id if self.run else None,
            agent_name=self.agent_name,
            action=action,
            prospect_id=prospect_id,
            contact_id=contact_id,
            details=json.dumps(details) if details else None,
            requires_review=requires_review,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def emit_event(self, event_type: str, payload: dict):
        """Emit an event for WebSocket broadcast.

        In Phase 1, this is a placeholder. In later phases, this will
        integrate with the WebSocket manager.
        """
        # TODO: Integrate with websocket.broadcast()
        pass

    def update_heartbeat(self):
        """Update the agent's heartbeat timestamp.

        In Phase 1, this is a placeholder. The Orchestrator will use
        heartbeats to monitor agent health.
        """
        # TODO: Implement heartbeat mechanism
        pass

    @abstractmethod
    def run_cycle(self) -> dict:
        """Execute one cycle of the agent's main loop.

        This method should be implemented by each agent subclass.

        Returns:
            A dict with summary information about what was done.
        """
        pass

    def execute(self, trigger: str = "scheduled") -> dict:
        """Execute the agent with proper lifecycle management.

        This is the main entry point for running an agent.

        Args:
            trigger: What triggered this run ('scheduled', 'manual', 'event')

        Returns:
            A dict with run results and summary.
        """
        self.start_run(trigger)

        try:
            result = self.run_cycle()
            self.complete_run()
            return {
                "success": True,
                "run_id": self.run.id,
                "result": result,
            }
        except Exception as e:
            self.fail_run(e)
            return {
                "success": False,
                "run_id": self.run.id if self.run else None,
                "error": str(e),
            }
