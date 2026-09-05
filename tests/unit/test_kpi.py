import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.warehouse import load_df_to_warehouse
from backend.services.kpi_service import KPIService
from backend.database import SessionLocal
from backend.models import Metric, Workspace

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_orders_for_kpis():
    df = pd.DataFrame({
        "order_id": [1, 2, 3, 4],
        "amount": [1000.0, 2500.0, 500.0, 3000.0],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "promised_date": ["2026-01-05", "2026-01-05", "2026-01-05", "2026-01-05"],
        "delivery_date": ["2026-01-04", "2026-01-08", "2026-01-04", "2026-01-09"]  # 2 of 4 late = 50%
    })
    load_df_to_warehouse(df, "orders")

def test_kpi_evaluation_and_thresholds():
    db = SessionLocal()
    ws = db.query(Workspace).first()
    if not ws:
        ws = Workspace(name="Test WS")
        db.add(ws)
        db.commit()

    import uuid
    code = f"LATE_TEST_{uuid.uuid4().hex[:6]}"
    metric = Metric(
        workspace_id=ws.id,
        name="Late Delivery Rate Test",
        code=code,
        source_table="orders",
        formula="AVG(CASE WHEN delivery_date > promised_date THEN 1.0 ELSE 0.0 END) * 100",
        time_column="order_date",
        target_value=5.0,
        warning_threshold=10.0,
        critical_threshold=25.0,
        comparison_direction="lower_is_better"
    )
    db.add(metric)
    db.commit()

    evaluated = KPIService.evaluate_metric(metric, period="this_month", db=db)
    assert evaluated.current_value == 50.0
    assert evaluated.status == "CRITICAL"  # 50% > 25% critical threshold
    assert len(evaluated.sparkline) > 0
    db.close()

def test_test_formula_helper():
    res = KPIService.test_formula("orders", "SUM(amount)")
    assert res["success"] is True
    assert res["sample_result"] == 7000.0

def test_metrics_api():
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    metrics_list = resp.json()
    assert len(metrics_list) > 0
    # Revenue metric should exist
    rev = next((m for m in metrics_list if "REV" in m["code"]), None)
    if rev:
        assert rev["current_value"] == 7000.0
