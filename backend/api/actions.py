from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.schemas.action import (
    ActionItemCreate, ActionApprovalRequest, ActionItemResponse
)
from backend.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["actions"])

@router.get("", response_model=List[ActionItemResponse])
def list_actions(
    status: Optional[str] = Query(None, description="Filter by status: PROPOSED, APPROVED, IN_PROGRESS, COMPLETED, REJECTED"),
    priority: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Returns prioritized operational actions requiring review or execution.
    """
    return ActionService.list_actions(db, status=status, priority=priority, owner=owner, limit=limit)

@router.post("", response_model=ActionItemResponse, status_code=201)
def create_action(
    payload: ActionItemCreate,
    db: Session = Depends(get_db)
):
    """
    Proposes a new action item (from exception, copilot, or manual entry).
    """
    return ActionService.create_action(db, payload)

@router.get("/{action_id}", response_model=ActionItemResponse)
def get_action(
    action_id: str,
    db: Session = Depends(get_db)
):
    action = ActionService.get_action_by_id(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action

@router.post("/{action_id}/approve", response_model=ActionItemResponse)
def approve_action(
    action_id: str,
    request: Optional[ActionApprovalRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Human Approval Gate: Approves a proposed action item.
    """
    req = request or ActionApprovalRequest(action="approve", approved_by="Operations Lead")
    req.action = "approve"
    try:
        return ActionService.approve_or_reject(db, action_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{action_id}/reject", response_model=ActionItemResponse)
def reject_action(
    action_id: str,
    request: ActionApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Human Approval Gate: Rejects a proposed action item with required explanation.
    """
    request.action = "reject"
    try:
        return ActionService.approve_or_reject(db, action_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{action_id}/execute")
def execute_action(
    action_id: str,
    executed_by: str = Query("Operations Lead"),
    db: Session = Depends(get_db)
):
    """
    Executes an approved action item safely (e.g. export CSV, draft email, call list, create internal task).
    Never executes business alterations without prior approval.
    """
    try:
        result = ActionService.execute_action(db, action_id, executed_by=executed_by)
        return {
            "status": "SUCCESS",
            "action_id": action_id,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
