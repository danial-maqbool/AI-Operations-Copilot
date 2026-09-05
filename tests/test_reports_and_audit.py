import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_generate_and_download_report():
    # 1. Generate Report
    resp = client.post("/api/reports/generate", json={
        "title": "Weekly Executive Operations Summary",
        "period": "Weekly",
        "report_type": "EXECUTIVE",
        "include_kpis": True,
        "include_exceptions": True,
        "include_actions": True,
        "include_sla": True
    })
    assert resp.status_code == 201
    rep = resp.json()
    assert rep["title"] == "Weekly Executive Operations Summary"
    assert "xlsx" in rep["download_urls"]
    assert "json" in rep["download_urls"]
    assert "csv" in rep["download_urls"]

    report_id = rep["id"]

    # 2. Get Report by ID
    get_resp = client.get(f"/api/reports/{report_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == report_id

    # 3. List Reports
    list_resp = client.get("/api/reports")
    assert list_resp.status_code == 200
    assert any(r["id"] == report_id for r in list_resp.json())

    # 4. Download XLSX
    xlsx_url = rep["download_urls"]["xlsx"]
    filename = xlsx_url.split("/")[-1]
    dl_resp = client.get(f"/api/reports/download/{filename}")
    assert dl_resp.status_code == 200
    assert len(dl_resp.content) > 1000  # Excel file has substantial size

    # 5. Download CSV
    csv_url = rep["download_urls"]["csv"]
    csv_filename = csv_url.split("/")[-1]
    dl_csv = client.get(f"/api/reports/download/{csv_filename}")
    assert dl_csv.status_code == 200
    assert b"REPORT_TYPE" in dl_csv.content

def test_audit_log_and_stats():
    # Fetch audit log
    resp = client.get("/api/audit?limit=20")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)

    # Fetch audit stats
    stats_resp = client.get("/api/audit/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_audit_events" in stats
    assert "reports_generated" in stats
    assert stats["reports_generated"] >= 1
