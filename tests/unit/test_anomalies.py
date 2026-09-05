import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.warehouse import load_df_to_warehouse
from backend.services.anomaly_service import AnomalyDetectionService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_metrics_for_anomalies():
    # 20 normal values around 100 + 1 massive spike (1000)
    amounts = [100.0 + (i % 5) * 2 for i in range(20)] + [1000.0]
    costs = [70.0 + (i % 5) * 1.5 for i in range(20)] + [850.0]
    dates = pd.date_range("2026-01-01", periods=21, freq="D").strftime("%Y-%m-%d").tolist()
    ids = [f"TX-{i+1}" for i in range(21)]
    
    df = pd.DataFrame({
        "transaction_id": ids,
        "amount": amounts,
        "cost": costs,
        "order_date": dates
    })
    load_df_to_warehouse(df, "transactions")

def test_zscore_detection():
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(21)],
        "amount": [100.0 + (i % 5) * 2 for i in range(20)] + [1000.0]
    })
    anomalies = AnomalyDetectionService.detect_zscore(df, "amount", "transactions", threshold=3.0)
    assert len(anomalies) == 1
    assert anomalies[0].observed_value == 1000.0
    assert anomalies[0].method == "z_score"
    assert anomalies[0].is_verified_impact is False  # Must be labelled hypothesis
    assert len(anomalies[0].potential_drivers) > 0

def test_iqr_detection():
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(21)],
        "amount": [100.0 + (i % 5) * 2 for i in range(20)] + [1000.0]
    })
    anomalies = AnomalyDetectionService.detect_iqr(df, "amount", "transactions", multiplier=1.5)
    assert len(anomalies) >= 1
    assert any(a.observed_value == 1000.0 for a in anomalies)

def test_rolling_deviation():
    dates = pd.date_range("2026-01-01", periods=21, freq="D").strftime("%Y-%m-%d").tolist()
    amounts = [100.0 + (i % 3) for i in range(20)] + [900.0]
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(21)],
        "amount": amounts,
        "order_date": dates
    })
    anomalies = AnomalyDetectionService.detect_rolling_deviation(df, "amount", "order_date", "transactions", window=7)
    assert len(anomalies) >= 1
    assert anomalies[-1].observed_value == 900.0

def test_scan_api_endpoint():
    resp = client.post("/api/anomalies/scan", json={
        "table_name": "transactions",
        "method": "z_score",
        "threshold": 3.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["anomalies_detected"] >= 1
    assert data["items"][0]["observed_value"] == 1000.0
