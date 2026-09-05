import pytest
from backend.database import SessionLocal, init_db
from backend.services.rag_service import RAGService

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_rag_benchmark_01_refund_threshold(db):
    results = RAGService.search_knowledge_base(
        query="What is the dollar threshold for refunds requiring executive approval?",
        workspace_id=None,
        db=db,
        top_k=3
    )
    assert len(results) > 0
    top = results[0]
    assert "Refund_and_Credit_Policy" in top.document_name
    assert "$5,000" in top.content or "5,000" in top.content
    assert top.citation is not None
    assert "page" in top.citation.lower()

def test_rag_benchmark_02_credit_hold_timeline(db):
    results = RAGService.search_knowledge_base(
        query="When is a customer account placed on Credit Hold for overdue invoices?",
        workspace_id=None,
        db=db,
        top_k=3
    )
    assert len(results) > 0
    top = results[0]
    assert "Accounts_Receivable" in top.document_name
    assert "30 Days Overdue" in top.content or "Credit Hold" in top.content

def test_rag_benchmark_03_critical_ticket_sla(db):
    results = RAGService.search_knowledge_base(
        query="What is the target resolution time for Critical priority customer tickets?",
        workspace_id=None,
        db=db,
        top_k=3
    )
    assert len(results) > 0
    top = results[0]
    assert "Customer_Support_SLA_Policy" in top.document_name
    assert "4 hours" in top.content or "Critical" in top.content

def test_rag_benchmark_04_safety_stock_formula(db):
    results = RAGService.search_knowledge_base(
        query="How is warehouse safety stock formula calculated?",
        workspace_id=None,
        db=db,
        top_k=3
    )
    assert len(results) > 0
    top = results[0]
    assert "Inventory_Reorder" in top.document_name
    assert "Safety Stock" in top.content or "Lead Time" in top.content

def test_rag_benchmark_05_credit_hold_override_authority(db):
    results = RAGService.search_knowledge_base(
        query="Who has the authority to approve an override to release shipments on Credit Hold?",
        workspace_id=None,
        db=db,
        top_k=3
    )
    assert len(results) > 0
    top = results[0]
    assert "Accounts_Receivable" in top.document_name
    assert "Chief Financial Officer" in top.content
