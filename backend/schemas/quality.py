from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QualityFinding(BaseModel):
    table_name: str
    column_name: Optional[str] = None
    finding_type: str  # missing_value, duplicate_pk, duplicate_row, invalid_date, negative_value, impossible_pct, inconsistent_category, orphaned_fk
    severity: str  # INFO, WARNING, CRITICAL
    description: str
    affected_count: int
    affected_percentage: float
    evidence_samples: List[Any] = []

class ComponentHealthScore(BaseModel):
    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    referential_integrity: float
    overall_score: float
    formula_explanation: str

class TableQualityReport(BaseModel):
    table_name: str
    row_count: int
    health_score: float
    component_scores: ComponentHealthScore
    findings: List[QualityFinding]

class WorkspaceQualitySummary(BaseModel):
    workspace_id: str
    overall_data_health_score: float
    total_findings: int
    critical_findings: int
    warning_findings: int
    table_reports: List[TableQualityReport]
