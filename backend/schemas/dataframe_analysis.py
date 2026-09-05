from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GroupByRequest(BaseModel):
    table_name: str
    group_cols: List[str]
    aggregations: Dict[str, List[str]]  # e.g. {"amount": ["sum", "mean", "count"]}

class PivotRequest(BaseModel):
    table_name: str
    index_col: str
    columns_col: str
    values_col: str
    agg_func: str = "sum"

class CorrelationRequest(BaseModel):
    table_name: str
    numeric_cols: Optional[List[str]] = None

class RollingRequest(BaseModel):
    table_name: str
    date_col: str
    value_col: str
    window: int = 7

class TimeSeriesRequest(BaseModel):
    table_name: str
    date_col: str
    value_col: str
    frequency: str = "D"  # D, W, M
    agg_func: str = "sum"

class AnalysisResult(BaseModel):
    operation: str
    table_name: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_records: int
    summary_stats: Dict[str, Any] = {}
