import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.quality_service import DataQualityEngine
from backend.services.warehouse import load_df_to_warehouse
from backend.database import SessionLocal
from backend.models import DataCatalogColumn, Workspace

client = TestClient(app)

def test_data_quality_anomaly_detection():
    # Construct dataframe with deliberate defects
    df_dirty = pd.DataFrame({
        "order_id": [1, 2, 2, 4, None],  # duplicate PK (2) + unexpected null PK
        "customer_id": [10, 20, 30, 40, 50],
        "unit_price": [25.0, -10.0, 50.0, 30.0, 15.0],  # negative price (-10)
        "discount_pct": [10.0, 15.0, 150.0, 5.0, -5.0],  # impossible percentages (>100 and <0)
        "status": ["Pending", "pending", "PENDING", "Shipped", "Delivered"],  # inconsistent categories
        "order_date": ["2026-01-01", "not_a_date", "2026-01-03", "2026-01-04", "2026-01-05"]  # invalid date
    })
    load_df_to_warehouse(df_dirty, "dirty_orders")
    
    # Fake catalog column with PK definition
    pk_col = DataCatalogColumn(column_name="order_id", is_primary_key=True)
    other_cols = [
        DataCatalogColumn(column_name="unit_price"),
        DataCatalogColumn(column_name="discount_pct"),
        DataCatalogColumn(column_name="status"),
        DataCatalogColumn(column_name="order_date")
    ]
    
    report = DataQualityEngine.audit_table("dirty_orders", [pk_col] + other_cols)
    findings = report["findings"]
    finding_types = [f["finding_type"] for f in findings]
    
    assert "unexpected_null_pk" in finding_types
    assert "duplicate_pk" in finding_types
    assert "negative_value" in finding_types
    assert "impossible_pct" in finding_types
    assert "inconsistent_category" in finding_types
    assert "invalid_date" in finding_types
    
    # Test scoring formula
    scores = DataQualityEngine.calculate_health_scores(findings, 5, 6)
    assert scores.overall_score < 100.0
    assert "OpsPilot Data Health Score Formula" in scores.formula_explanation

def test_quality_audit_endpoint():
    resp = client.get("/api/quality/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_data_health_score" in data
    assert "table_reports" in data
