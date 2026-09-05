from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MetricBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    source_table: str
    formula: str
    time_column: Optional[str] = None
    aggregation: str = "sum"
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_direction: str = "higher_is_better"  # higher_is_better, lower_is_better
    owner: str = "Operations Team"

class MetricCreate(MetricBase):
    workspace_id: Optional[str] = None

class MetricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    formula: Optional[str] = None
    time_column: Optional[str] = None
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_direction: Optional[str] = None
    owner: Optional[str] = None

class SparklinePoint(BaseModel):
    label: str
    value: float

class MetricResponse(MetricBase):
    id: str
    workspace_id: str
    current_value: float = 0.0
    previous_value: float = 0.0
    abs_change: float = 0.0
    pct_change: float = 0.0
    status: str = "GOOD"  # GOOD, WARNING, CRITICAL
    sparkline: List[SparklinePoint] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TestMetricRequest(BaseModel):
    source_table: str
    formula: str
    time_column: Optional[str] = None
