from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ColumnProfile(BaseModel):
    id: Optional[str] = None
    table_id: Optional[str] = None
    table_name: str
    column_name: str
    data_type: str
    inferred_role: str
    user_role_override: Optional[str] = None
    inferred_description: Optional[str] = None
    user_description_override: Optional[str] = None
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    sample_values: List[Any] = []
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_sensitive: bool = False
    stats: Dict[str, Any] = {}

class TableProfile(BaseModel):
    id: str
    data_source_id: str
    table_name: str
    row_count: int
    column_count: int
    missing_cells_total: int
    duplicate_rows: int
    date_range: Optional[Dict[str, Optional[str]]] = None
    detected_entity: Optional[str] = None
    columns: List[ColumnProfile] = []
    data_health_score: float = 100.0

class RelationshipResponse(BaseModel):
    id: str
    source_table_name: str
    source_column_name: str
    target_table_name: str
    target_column_name: str
    confidence_score: float
    detection_method: str
    is_verified: bool

    class Config:
        from_attributes = True

class ColumnOverrideRequest(BaseModel):
    user_role_override: Optional[str] = None
    user_description_override: Optional[str] = None
    is_sensitive: Optional[bool] = None

class EntityDetectionSummary(BaseModel):
    table_name: str
    entity: str
    confidence: float
    rationale: str
