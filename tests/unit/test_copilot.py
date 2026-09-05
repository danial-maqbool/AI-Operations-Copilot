import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.warehouse import load_df_to_warehouse
from backend.services.rag_service import RAGService
from backend.services.pii_redactor import PIIRedactor
from backend.database import SessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_copilot_data(tmp_path):
    df_orders = pd.DataFrame({
        "order_id": [101, 102, 103, 104],
        "customer_id": ["C1", "C2", "C1", "C3"],
        "amount": [1200.0, 4500.0, 300.0, 2800.0],
        "promised_date": ["2026-01-05", "2026-01-05", "2026-01-05", "2026-01-05"],
        "delivery_date": ["2026-01-09", "2026-01-12", "2026-01-04", "2026-01-10"],  # 3 late
        "status": ["delayed", "delayed", "delivered", "delayed"]
    })
    load_df_to_warehouse(df_orders, "orders")

    df_invoices = pd.DataFrame({
        "invoice_id": ["INV-1", "INV-2", "INV-3"],
        "customer_id": ["C1", "C2", "C3"],
        "unpaid_amount": [4200.0, 1500.0, 8900.0],  # 2 over ,500
        "due_date": ["2025-11-01", "2026-03-01", "2025-12-01"],
        "status": ["refund_pending", "pending", "overdue"]
    })
    load_df_to_warehouse(df_invoices, "invoices")

    # Ingest refund policy
    policy_file = tmp_path / "Refund_Policy.md"
    policy_file.write_text("""# Refund Guidelines
Manager approval is required for all refund requests exceeding ,500 or cases open for more than 30 days.
""", encoding="utf-8")
    db = SessionLocal()
    RAGService.ingest_document(policy_file, "Refund_Policy.md", None, db)
    db.close()

def test_pii_redactor():
    text = "Please follow up with customer john.doe@example.com at (555) 123-4567 regarding order 101."
    redacted, mapping = PIIRedactor.redact(text)
    assert "[EMAIL_1]" in redacted
    assert "john.doe@example.com" not in redacted
    restored = PIIRedactor.restore(redacted, mapping)
    assert restored == text

def test_copilot_delayed_orders_query():
    resp = client.post("/api/copilot/chat", json={
        "question": "Which orders are delayed?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data["data_used"]
    assert len(data["sql_queries"]) > 0
    assert data["table_data"] is not None
    assert data["table_data"]["total_rows"] == 3
    assert len(data["recommended_actions"]) > 0
    assert "run_readonly_sql" in data["tools_executed"]

def test_copilot_investigation_query():
    resp = client.post("/api/copilot/chat", json={
        "question": "Why did delivery delays increase?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "investigate_problem" in data["tools_executed"]
    assert "Investigation" in data["direct_answer"]
    assert len(data["recommended_actions"]) > 0

def test_copilot_hybrid_rag_and_sql():
    resp = client.post("/api/copilot/chat", json={
        "question": "Which refund cases require manager approval according to our policy?"
    })
    assert resp.status_code == 200
    data = resp.json()
    # Confirms both RAG and SQL were executed
    assert "search_documents" in data["tools_executed"]
    assert "run_readonly_sql" in data["tools_executed"]
    assert len(data["policy_citations"]) > 0
    assert "Refund_Policy.md" in str(data["policy_citations"])
    assert data["table_data"]["total_rows"] == 2  # INV-1 () and INV-3 ()
    assert len(data["recommended_actions"]) > 0
