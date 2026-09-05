from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReportGenerateRequest(BaseModel):
    title: str = "Executive Operations Report"
    period: str = "Weekly"  # Daily, Weekly, Monthly, Custom
    report_type: str = "EXECUTIVE"  # EXECUTIVE, FINANCIAL, FULFILLMENT, INVENTORY
    include_kpis: bool = True
    include_exceptions: bool = True
    include_actions: bool = True
    include_sla: bool = True

class ReportResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    period: str
    report_type: str
    sections: Dict[str, Any] = {}
    export_formats: List[str] = ["xlsx", "json", "csv"]
    file_path: Optional[str] = None
    download_urls: Dict[str, str] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class AuditEventResponse(BaseModel):
    id: str
    workspace_id: str
    event_type: str
    user_name: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Dict[str, Any] = {}
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
