import pytest
import os
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, init_db
from backend.models.all_models import ActionItem, AuditEvent, OperationsException
from backend.services.action_service import ActionService
from backend.services.entity_views import EntityViewService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_action_lifecycle_and_approval_gate():
    # 1. Create action
    resp = client.post("/api/actions", json={
        "title": "Contact Acme Corp regarding Overdue Invoices",
        "description": "Invoice INV-9021 is 18 days overdue with $4,500 outstanding",
        "reason": "Payment overdue exceeds 14 days standard threshold",
        "priority": "HIGH",
        "owner": "Finance Specialist",
        "action_type": "draft_email",
        "suggested_steps": ["Review customer ledger", "Send reminder email with payment link"],
        "affected_records": [
            {"customer_id": "CUST-001", "email": "billing@acmecorp.com", "amount": 4500.0}
        ],
        "approval_required": True
    })
    assert resp.status_code == 201
    action_data = resp.json()
    action_id = action_data["id"]
    assert action_data["status"] == "PROPOSED"
    assert action_data["action_type"] == "draft_email"

    # 2. Execution before approval must fail
    fail_exec = client.post(f"/api/actions/{action_id}/execute")
    assert fail_exec.status_code == 400
    assert "must be APPROVED first" in fail_exec.json()["detail"]

    # 3. Approve action
    appr_resp = client.post(f"/api/actions/{action_id}/approve", json={
        "action": "approve",
        "approved_by": "Senior Operations Manager"
    })
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"
    assert appr_resp.json()["approved_by"] == "Senior Operations Manager"

    # 4. Execute approved action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()["result"]
    assert exec_data["execution_type"] == "draft_email"
    assert exec_data["recipient"] == "billing@acmecorp.com"
    assert "URGENT OPS UPDATE" in exec_data["subject"]

    # 5. Check action status now COMPLETED
    get_resp = client.get(f"/api/actions/{action_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "COMPLETED"

def test_action_rejection_flow():
    resp = client.post("/api/actions", json={
        "title": "Cancel shipment SH-999",
        "description": "Suspicious delayed order",
        "priority": "CRITICAL",
        "action_type": "create_task",
        "approval_required": True
    })
    assert resp.status_code == 201
    action_id = resp.json()["id"]

    # Reject
    rej_resp = client.post(f"/api/actions/{action_id}/reject", json={
        "action": "reject",
        "rejection_reason": "Carrier verified shipment is on schedule despite delay flag",
        "approved_by": "Logistics Lead"
    })
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"
    assert rej_resp.json()["rejection_reason"] == "Carrier verified shipment is on schedule despite delay flag"

def test_action_export_csv_execution():
    resp = client.post("/api/actions", json={
        "title": "Export High Risk Customers",
        "action_type": "export_csv",
        "approval_required": False,
        "affected_records": [
            {"customer_id": "CUST-10", "name": "Global Corp", "risk": "HIGH"},
            {"customer_id": "CUST-20", "name": "Beta LLC", "risk": "CRITICAL"}
        ]
    })
    assert resp.status_code == 201
    action_id = resp.json()["id"]

    # Execute directly since approval_required is False
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 200
    result = exec_resp.json()["result"]
    assert result["execution_type"] == "export_csv"
    assert result["records_exported"] == 2
    assert os.path.exists(result["file_path"])

def test_sla_risk_monitor_and_entity_views():
    # SLA Monitor endpoint
    resp = client.get("/api/entities/sla-monitor")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "breached_count" in data["summary"]
    assert "financial_exposure" in data["summary"]

    # Customer 360
    cust_resp = client.get("/api/entities/customer/CUST-TEST-999")
    assert cust_resp.status_code == 200
    cust_data = cust_resp.json()
    assert "metrics" in cust_data
    assert "health_score" in cust_data["metrics"]

    # Order 360
    ord_resp = client.get("/api/entities/order/ORD-TEST-999")
    assert ord_resp.status_code == 200
    ord_data = ord_resp.json()
    assert "order" in ord_data
    assert "sla" in ord_data
