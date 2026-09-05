from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    sql: str
    workspace_id: Optional[str] = None
    explain: bool = True

class QueryResponse(BaseModel):
    success: bool
    sql: str
    sanitized_sql: str
    explanation: Optional[str] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    total_rows: int = 0
    duration_ms: float = 0.0
    referenced_tables: List[str] = []
    error: Optional[str] = None
