from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CopilotChatRequest(BaseModel):
    question: str
    workspace_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChartSpec(BaseModel):
    chart_type: str  # bar, line, pie, donut, scatter, table
    title: str
    x_key: str
    y_key: str
    data: List[Dict[str, Any]]

class CopilotActionRecommendation(BaseModel):
    title: str
    description: str
    reason: str
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    owner: str = "Operations Manager"
    action_type: str = "create_task"  # create_task, export_csv, draft_email, call_list, status_update
    suggested_steps: List[str] = []
    approval_required: bool = True

class CopilotResponse(BaseModel):
    conversation_id: str
    message_id: str
    direct_answer: str
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW
    data_used: List[str] = []
    filters_applied: List[str] = []
    calculations: Dict[str, Any] = {}
    table_data: Optional[Dict[str, Any]] = None
    chart: Optional[ChartSpec] = None
    sql_queries: List[Dict[str, Any]] = []
    policy_citations: List[Dict[str, Any]] = []
    recommended_actions: List[CopilotActionRecommendation] = []
    evidence: Dict[str, Any] = {}
    tools_executed: List[str] = []
