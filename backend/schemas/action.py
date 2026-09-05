from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ActionItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    source_finding: Optional[str] = None
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    owner: str = "Operations Lead"
    due_date: Optional[datetime] = None
    action_type: str = "create_task"  # create_task, export_csv, draft_email, call_list, status_update
    suggested_steps: List[str] = []
    affected_records: List[Dict[str, Any]] = []
    approval_required: bool = True

class ActionItemCreate(ActionItemBase):
    workspace_id: Optional[str] = None
    exception_id: Optional[str] = None

class ActionApprovalRequest(BaseModel):
    action: str  # approve, reject
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = "Operations Manager"

class ActionItemResponse(ActionItemBase):
    id: str
    workspace_id: str
    exception_id: Optional[str] = None
    status: str  # PROPOSED, APPROVED, IN_PROGRESS, COMPLETED, REJECTED
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    execution_result: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
