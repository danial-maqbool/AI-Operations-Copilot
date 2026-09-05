import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_load_demo_company():
    resp = client.post("/api/demo/load")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["total_tables_loaded"] >= 10
    assert data["total_rows_loaded"] >= 4000
    assert data["documents_indexed"] >= 4
    assert "customers" in data["table_breakdown"]
    assert "orders" in data["table_breakdown"]
    assert "invoices" in data["table_breakdown"]
    assert "inventory" in data["table_breakdown"]
    assert "support_tickets" in data["table_breakdown"]

    # Verify that data catalog has tables
    cat_resp = client.get("/api/catalog/tables")
    assert cat_resp.status_code == 200
    tables = cat_resp.json()
    assert len(tables) >= 10

    # Verify that metrics catalog has metrics
    kpi_resp = client.get("/api/metrics")
    assert kpi_resp.status_code == 200
    kpis = kpi_resp.json()
    assert len(kpis) >= 5

    # Verify that exceptions were triggered
    exc_resp = client.get("/api/exceptions")
    assert exc_resp.status_code == 200
    exceptions = exc_resp.json()
    assert len(exceptions) >= 1
