import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.profiler_service import ProfilerService
from backend.services.warehouse import load_df_to_warehouse
from backend.database import SessionLocal
from backend.models import DataSource, DataSourceTable, Workspace

client = TestClient(app)

def test_column_profiling():
    series = pd.Series([101, 102, 103, 104, 105])
    profile = ProfilerService.profile_column(series, "order_id", "orders")
    
    assert profile["column_name"] == "order_id"
    assert profile["null_count"] == 0
    assert profile["unique_count"] == 5
    assert profile["is_primary_key"] is True
    assert profile["inferred_role"] == "identifier"

def test_entity_detection():
    cols = ["customer_id", "customer_name", "email", "created_at"]
    entity, conf, reason = ProfilerService.detect_table_entity("company_customers", cols)
    assert entity == "Customers"
    assert conf >= 0.8

def test_catalog_profile_and_relationships():
    # Setup test tables in warehouse
    df_cust = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "name": ["Acme", "Globex", "Initech"],
        "email": ["a@acme.com", "b@globex.com", "c@initech.com"]
    })
    df_orders = pd.DataFrame({
        "order_id": [101, 102, 103],
        "customer_id": [1, 2, 1],
        "amount": [500.0, 150.0, 320.0],
        "status": ["delivered", "delayed", "pending"]
    })
    load_df_to_warehouse(df_cust, "customers")
    load_df_to_warehouse(df_orders, "orders")

    # Ingest data sources via API
    resp = client.get("/api/catalog/profile")
    assert resp.status_code == 200
    profiles = resp.json()
    assert len(profiles) >= 2

    # Check relationships
    rel_resp = client.get("/api/catalog/relationships")
    assert rel_resp.status_code == 200
    relationships = rel_resp.json()
    assert any(
        r["source_table_name"] == "orders" and 
        r["source_column_name"] == "customer_id" and 
        r["target_table_name"] == "customers"
        for r in relationships
    )
