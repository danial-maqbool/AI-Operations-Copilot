import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.warehouse import load_df_to_warehouse
from backend.services.rule_engine import BusinessRuleEngine
from backend.database import SessionLocal
from backend.models import BusinessRule, OperationsException, Workspace

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_invoices_for_rules():
    df = pd.DataFrame({
        "invoice_id": ["INV-1001", "INV-1002", "INV-1003", "INV-1004"],
        "customer": ["Acme", "Globex", "Initech", "Umbrella"],
        "unpaid_amount": [12000.0, 450.0, 8500.0, 0.0],
        "due_date": ["2025-11-01", "2026-03-01", "2025-12-15", "2026-01-01"],
        "status": ["overdue", "pending", "overdue", "paid"]
    })
    load_df_to_warehouse(df, "invoices")

def test_condition_evaluation():
    df = pd.DataFrame({
        "amount": [100, 500, 1000],
        "category": ["Alpha", "Beta", "Gamma"],
        "tag": [None, "urgent", ""]
    })
    # Greater than
    mask_gt = BusinessRuleEngine.evaluate_condition(df, {"field": "amount", "operator": "greater_than", "value": 400})
    assert mask_gt.tolist() == [False, True, True]

    # Contains
    mask_cont = BusinessRuleEngine.evaluate_condition(df, {"field": "category", "operator": "contains", "value": "bet"})
    assert mask_cont.tolist() == [False, True, False]

    # Is Empty
    mask_empty = BusinessRuleEngine.evaluate_condition(df, {"field": "tag", "operator": "is_empty", "value": None})
    assert mask_empty.tolist() == [True, False, True]

def test_priority_score_formula():
    # Critical severity (40) +  financial (25) + 60 days (20) + SLA risk (15) = 100.0
    score = BusinessRuleEngine.calculate_priority_score(
        severity="CRITICAL",
        financial_impact=10000.0,
        age_days=60,
        sla_at_risk=True
    )
    assert score == 100.0

    # Low severity (10) + no financial (0) + 0 days (0) + no SLA (0) = 10.0
    score_low = BusinessRuleEngine.calculate_priority_score(
        severity="LOW",
        financial_impact=0.0,
        age_days=0,
        sla_at_risk=False
    )
    assert score_low == 10.0

def test_rule_evaluation_and_exceptions():
    db = SessionLocal()
    ws = db.query(Workspace).first()
    if not ws:
        ws = Workspace(name="Test WS")
        db.add(ws)
        db.commit()

    rule = BusinessRule(
        workspace_id=ws.id,
        name="Large Overdue Balance",
        entity="invoice",
        target_table="invoices",
        severity="CRITICAL",
        conditions=[
            {"field": "unpaid_amount", "operator": "greater_than", "value": 5000.0},
            {"field": "status", "operator": "equals", "value": "overdue"}
        ],
        action_template={"title": "Collect high-value overdue debt"},
        is_active=True
    )
    db.add(rule)
    db.commit()

    created_exc = BusinessRuleEngine.evaluate_rule(rule, db)
    # INV-1001 (12000.0) and INV-1003 (8500.0) match
    assert len(created_exc) == 2
    assert any(e.entity_id == "INV-1001" for e in created_exc)
    assert any(e.entity_id == "INV-1003" for e in created_exc)
    assert created_exc[0].priority_score >= 60.0  # Critical + high financial impact

    # Test Exception API and status transition
    exc_id = created_exc[0].id
    patch_resp = client.patch(f"/api/exceptions/{exc_id}", json={"status": "ACKNOWLEDGED"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ACKNOWLEDGED"

    db.close()
