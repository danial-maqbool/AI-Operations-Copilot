from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DataSourceBase(BaseModel):
    name: str
    source_type: str
    connection_uri: Optional[str] = None
    file_path: Optional[str] = None

class DataSourceCreate(DataSourceBase):
    workspace_id: Optional[str] = None

class TableSummary(BaseModel):
    id: str
    table_name: str
    row_count: int
    column_count: int
    sheet_name: Optional[str] = None
    data_health_score: float = 100.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DataSourceResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    source_type: str
    connection_uri: Optional[str] = None
    status: str
    row_count: int
    table_count: int
    last_refreshed: datetime
    created_at: datetime
    tables: List[TableSummary] = []

    class Config:
        from_attributes = True

class PostgresConnectRequest(BaseModel):
    name: str
    connection_uri: str
    workspace_id: Optional[str] = None
