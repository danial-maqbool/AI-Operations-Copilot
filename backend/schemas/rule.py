from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RuleCondition(BaseModel):
    field: str
    operator: str  # equals, not_equals, greater_than, less_than, greater_than_or_equal, less_than_or_equal, contains, before, after, is_empty, is_not_empty
    value: Any

class BusinessRuleCreate(BaseModel):
    workspace_id: Optional[str] = None
    name: str
    entity: str
    target_table: str
    conditions: List[RuleCondition]
    severity: str = "HIGH"  # INFO, WARNING, HIGH, CRITICAL
    action_template: Optional[Dict[str, Any]] = None
    is_active: bool = True

class BusinessRuleResponse(BusinessRuleCreate):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExceptionResponse(BaseModel):
    id: str
    workspace_id: str
    rule_id: Optional[str] = None
    exception_type: str
    severity: str
    entity_type: str
    entity_id: str
    title: str
    description: Optional[str] = None
    observed_value: Optional[str] = None
    financial_impact: float = 0.0
    sla_deadline: Optional[datetime] = None
    owner: str
    age_days: int = 0
    priority_score: float = 50.0
    status: str = "OPEN"
    evidence: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExceptionStatusUpdate(BaseModel):
    status: str  # OPEN, ACKNOWLEDGED, RESOLVED, IGNORED
