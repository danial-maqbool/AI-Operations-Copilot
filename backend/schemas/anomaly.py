from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AnomalyItem(BaseModel):
    table_name: str
    column_name: str
    method: str  # z_score, iqr, rolling_deviation, isolation_forest
    observed_value: float
    expected_range: Dict[str, float]  # min, max
    deviation: float
    deviation_percentage: float
    record_id: Optional[str] = None
    date: Optional[str] = None
    potential_drivers: List[str] = []
    is_verified_impact: bool = False
    details: Dict[str, Any] = {}

class AnomalyScanRequest(BaseModel):
    table_name: str
    columns: Optional[List[str]] = None
    method: str = "all"  # z_score, iqr, rolling, isolation_forest, all
    threshold: float = 3.0

class AnomalyScanResponse(BaseModel):
    table_name: str
    total_records_analyzed: int
    anomalies_detected: int
    items: List[AnomalyItem]
