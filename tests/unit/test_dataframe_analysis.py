import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.warehouse import load_df_to_warehouse
from backend.services.dataframe_service import DataFrameAnalysisService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_sales_table():
    df = pd.DataFrame({
        "order_id": [1, 2, 3, 4, 5, 6],
        "customer": ["Acme", "Globex", "Acme", "Initech", "Globex", "Acme"],
        "status": ["shipped", "delayed", "shipped", "delivered", "delayed", "shipped"],
        "amount": [100.0, 250.0, 300.0, 150.0, 400.0, 200.0],
        "cost": [70.0, 180.0, 210.0, 100.0, 290.0, 140.0],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"]
    })
    load_df_to_warehouse(df, "sales_data")

def test_groupby_analysis():
    res = DataFrameAnalysisService.group_by_analysis(
        table_name="sales_data",
        group_cols=["customer"],
        aggregations={"amount": ["sum", "count"]}
    )
    assert res.total_records == 3
    assert "amount_sum" in res.columns or any("sum" in c for c in res.columns)
    
    # Verify Acme's sum is 600.0 (100 + 300 + 200)
    acme_row = next(r for r in res.rows if r["customer"] == "Acme")
    sum_key = [k for k in acme_row.keys() if "sum" in k][0]
    assert acme_row[sum_key] == 600.0

def test_pivot_analysis():
    res = DataFrameAnalysisService.pivot_analysis(
        table_name="sales_data",
        index_col="customer",
        columns_col="status",
        values_col="amount",
        agg_func="sum"
    )
    assert res.total_records == 3
    assert "customer" in res.columns

def test_correlation_analysis():
    res = DataFrameAnalysisService.correlation_analysis(
        table_name="sales_data",
        numeric_cols=["amount", "cost"]
    )
    assert res.total_records == 2
    # Amount and cost should be positively correlated
    row = res.rows[0]
    assert "amount" in row
    assert row["amount"] > 0.9

def test_timeseries_aggregation():
    res = DataFrameAnalysisService.time_series_aggregation(
        table_name="sales_data",
        date_col="order_date",
        value_col="amount",
        frequency="D",
        agg_func="sum"
    )
    assert res.total_records >= 6

def test_analysis_api_endpoint():
    resp = client.post("/api/analysis/groupby", json={
        "table_name": "sales_data",
        "group_cols": ["status"],
        "aggregations": {"amount": ["sum"]}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records"] == 3
