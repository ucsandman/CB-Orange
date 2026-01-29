"""Agent management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database.connection import get_db
from database.models import AgentRun, AgentAuditLog, HygieneFlag, AGENT_NAMES
from api.schemas import APIResponse, AgentRunRead, AgentHealth, HygieneFlagRead

router = APIRouter()


@router.get("/health", response_model=APIResponse)
async def get_all_agent_health(db: Session = Depends(get_db)):
    """Get health status for all agents."""
    health_data = []
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    for agent_name in AGENT_NAMES:
        # Last run
        last_run = (
            db.query(AgentRun)
            .filter(AgentRun.agent_name == agent_name)
            .order_by(AgentRun.started_at.desc())
            .first()
        )

        # Runs in last 24h
        runs_24h = (
            db.query(AgentRun)
            .filter(
                AgentRun.agent_name == agent_name,
                AgentRun.started_at >= day_ago
            )
            .count()
        )

        # Errors in last 24h
        errors_24h = (
            db.query(AgentRun)
            .filter(
                AgentRun.agent_name == agent_name,
                AgentRun.started_at >= day_ago,
                AgentRun.status == 'failed'
            )
            .count()
        )

        # Determine health status
        if last_run is None:
            status = "unknown"
        elif last_run.status == "failed":
            status = "degraded"
        elif errors_24h > 2:
            status = "degraded"
        else:
            status = "healthy"

        health_data.append(AgentHealth(
            agent_name=agent_name,
            status=status,
            last_run_at=last_run.started_at if last_run else None,
            last_run_status=last_run.status if last_run else None,
            runs_last_24h=runs_24h,
            errors_last_24h=errors_24h,
        ))

    return APIResponse(data=health_data)


@router.get("/runs", response_model=APIResponse)
async def list_agent_runs(
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List agent runs with optional filters."""
    query = db.query(AgentRun)

    if agent_name:
        query = query.filter(AgentRun.agent_name == agent_name)
    if status:
        query = query.filter(AgentRun.status == status)

    total = query.count()
    runs = query.order_by(AgentRun.started_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "runs": [AgentRunRead.model_validate(r) for r in runs],
            "total": total,
        }
    )


@router.get("/runs/{run_id}", response_model=APIResponse)
async def get_agent_run(run_id: str, db: Session = Depends(get_db)):
    """Get details of a specific agent run."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    # Get audit logs for this run
    logs = (
        db.query(AgentAuditLog)
        .filter(AgentAuditLog.agent_run_id == run_id)
        .order_by(AgentAuditLog.created_at)
        .all()
    )

    return APIResponse(
        data={
            "run": AgentRunRead.model_validate(run),
            "audit_logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "prospect_id": log.prospect_id,
                    "details": log.details,
                    "created_at": log.created_at,
                }
                for log in logs
            ],
        }
    )


@router.post("/{agent_name}/trigger", response_model=APIResponse)
async def trigger_agent(agent_name: str, db: Session = Depends(get_db)):
    """Manually trigger an agent run."""
    if agent_name not in AGENT_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")

    # Create a new run record
    run = AgentRun(
        agent_name=agent_name,
        trigger="manual",
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # In a real implementation, this would queue the agent for execution
    # For now, we just return the run ID
    return APIResponse(
        data={
            "message": f"Agent {agent_name} triggered",
            "run_id": run.id,
        }
    )


@router.get("/flags", response_model=APIResponse)
async def list_hygiene_flags(
    prospect_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List hygiene flags."""
    query = db.query(HygieneFlag)

    if prospect_id:
        query = query.filter(HygieneFlag.prospect_id == prospect_id)
    if severity:
        query = query.filter(HygieneFlag.severity == severity)
    if resolved is not None:
        if resolved:
            query = query.filter(HygieneFlag.resolved_at.isnot(None))
        else:
            query = query.filter(HygieneFlag.resolved_at.is_(None))

    total = query.count()
    flags = query.order_by(HygieneFlag.created_at.desc()).offset(offset).limit(limit).all()

    return APIResponse(
        data={
            "flags": [HygieneFlagRead.model_validate(f) for f in flags],
            "total": total,
        }
    )


@router.post("/flags/{flag_id}/resolve", response_model=APIResponse)
async def resolve_hygiene_flag(
    flag_id: str,
    resolved_by: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Resolve a hygiene flag."""
    flag = db.query(HygieneFlag).filter(HygieneFlag.id == flag_id).first()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    if flag.resolved_at:
        raise HTTPException(status_code=400, detail="Flag already resolved")

    flag.resolved_at = datetime.utcnow()
    flag.resolved_by = resolved_by
    flag.resolution_notes = notes
    db.commit()
    db.refresh(flag)

    return APIResponse(data=HygieneFlagRead.model_validate(flag))
