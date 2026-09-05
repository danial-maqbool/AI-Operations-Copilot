from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.all_models import AuditEvent
from backend.schemas.report import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Log"])

@router.get("", response_model=List[AuditEventResponse])
def get_audit_log(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    user_name: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Returns audit trail of all operations actions, safe SQL queries, workflow runs, and report generations.
    """
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if user_name:
        query = query.filter(AuditEvent.user_name.ilike(f"%{user_name}%"))
    
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()

@router.get("/stats")
def get_audit_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns aggregated audit metrics.
    """
    total_events = db.query(func.count(AuditEvent.id)).scalar() or 0
    
    type_counts = dict(
        db.query(AuditEvent.event_type, func.count(AuditEvent.id))
        .group_by(AuditEvent.event_type)
        .all()
    )

    return {
        "total_audit_events": total_events,
        "event_breakdown": type_counts,
        "actions_proposed": type_counts.get("action_proposed", 0),
        "actions_approved": type_counts.get("action_approved", 0),
        "actions_rejected": type_counts.get("action_rejected", 0),
        "actions_executed": type_counts.get("action_executed", 0),
        "workflows_executed": type_counts.get("workflow_run", 0) + type_counts.get("morning_review_run", 0),
        "reports_generated": type_counts.get("report_generated", 0)
    }
