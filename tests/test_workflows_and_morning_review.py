import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_workflow_crud_and_execution():
    # 1. Create Workflow
    resp = client.post("/api/workflows", json={
        "name": "Daily Fulfillment Audit",
        "description": "Scans orders, checks SLA, computes KPIs",
        "trigger_type": "schedule",
        "steps": [
            {"step_id": "step-1", "name": "Sync KPIs", "step_type": "calculate_kpis"},
            {"step_id": "step-2", "name": "Scan SLA", "step_type": "check_sla_breaches"},
            {"step_id": "step-3", "name": "Evaluate Rules", "step_type": "evaluate_rules"}
        ],
        "is_active": True
    })
    assert resp.status_code == 201
    wf_data = resp.json()
    wf_id = wf_data["id"]
    assert wf_data["name"] == "Daily Fulfillment Audit"
    assert len(wf_data["steps"]) == 3

    # 2. List Workflows
    list_resp = client.get("/api/workflows")
    assert list_resp.status_code == 200
    assert any(w["id"] == wf_id for w in list_resp.json())

    # 3. Trigger Workflow Run
    run_resp = client.post(f"/api/workflows/{wf_id}/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["workflow_id"] == wf_id
    assert len(run_data["execution_log"]) == 3

    # 4. Update Workflow
    up_resp = client.put(f"/api/workflows/{wf_id}", json={
        "description": "Updated fulfillment audit description"
    })
    assert up_resp.status_code == 200
    assert up_resp.json()["description"] == "Updated fulfillment audit description"

    # 5. Delete Workflow
    del_resp = client.delete(f"/api/workflows/{wf_id}")
    assert del_resp.status_code == 204

def test_morning_operations_review():
    resp = client.post("/api/morning-review/run")
    assert resp.status_code == 200
    data = resp.json()
    
    assert "review_id" in data
    assert "data_health_score" in data
    assert "kpi_summary" in data
    assert "exceptions_summary" in data
    assert "sla_summary" in data
    assert "todays_prioritized_actions" in data
    assert "executive_brief" in data
    assert len(data["executive_brief"]) > 10
    assert data["duration_ms"] >= 0
