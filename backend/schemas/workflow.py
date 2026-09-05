from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WorkflowStep(BaseModel):
    step_id: str
    step_type: str  # refresh_sources, calculate_kpis, evaluate_rules, detect_anomalies, check_sla_breaches, generate_action_plan, generate_brief
    name: str
    parameters: Dict[str, Any] = {}

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str = "manual"  # manual, schedule, threshold
    steps: List[Dict[str, Any]] = []
    is_active: bool = True

class WorkflowCreate(WorkflowBase):
    workspace_id: Optional[str] = None

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    actions_created: int = 0
    error_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class WorkflowResponse(WorkflowBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    runs: List[WorkflowRunResponse] = []

    class Config:
        from_attributes = True

class MorningReviewResponse(BaseModel):
    review_id: str
    timestamp: str
    data_health_score: float
    kpi_summary: Dict[str, Any]
    exceptions_summary: Dict[str, Any]
    anomalies_summary: Dict[str, Any]
    sla_summary: Dict[str, Any]
    todays_prioritized_actions: List[Dict[str, Any]]
    executive_brief: str
    duration_ms: int
