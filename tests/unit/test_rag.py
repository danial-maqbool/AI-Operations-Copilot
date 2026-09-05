import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.rag_service import RAGService
from backend.database import SessionLocal
from backend.models import Document, Workspace

client = TestClient(app)

def test_markdown_policy_ingestion_and_search(tmp_path):
    policy_text = """# Company Refund Policy

## Section 1: Standard Returns
Customers may return items within 30 days of receipt for a full credit refund.

## Section 2: Manager Approvals
Any refund request older than 30 days or with an invoice amount exceeding ,500 requires explicit Tier-2 Operations Manager approval before processing.
Exceptions are strictly audited.

## Section 3: Damaged Goods
Damaged goods must have an inspection report attached prior to issuing any debit adjustment.
"""
    policy_file = tmp_path / "Refund_Policy.md"
    policy_file.write_text(policy_text, encoding="utf-8")

    db = SessionLocal()
    doc = RAGService.ingest_document(policy_file, "Refund_Policy.md", None, db)
    assert doc.id is not None
    assert doc.total_chunks >= 3
    assert doc.status == "INDEXED"

    # Test Search
    results = RAGService.search("When is manager approval required for refund?", None, db, top_k=2)
    assert len(results) > 0
    top_hit = results[0]
    assert "Manager Approvals" in (top_hit.section_title or "") or "manager approval" in top_hit.content.lower()
    assert "Refund_Policy.md" in top_hit.citation
    assert "Page:" in top_hit.citation
    assert "Section:" in top_hit.citation

    db.close()

def test_documents_api_upload_and_search(tmp_path):
    sop_file = tmp_path / "SLA_Policy.txt"
    sop_file.write_text("""SLA Guidelines:
Priority 1 Critical Incidents must be resolved within 4 hours.
Priority 2 High Incidents have an 8-hour target resolution SLA.
Failure to acknowledge within 30 minutes triggers automated escalation to the operations lead.
""", encoding="utf-8")

    with open(sop_file, "rb") as f:
        upload_resp = client.post("/api/documents/upload", files={"file": ("SLA_Policy.txt", f, "text/plain")})

    assert upload_resp.status_code == 200
    data = upload_resp.json()
    assert data["filename"] == "SLA_Policy.txt"

    # Search API
    search_resp = client.post("/api/documents/search", json={"query": "Priority 1 critical incident SLA", "top_k": 2})
    assert search_resp.status_code == 200
    hits = search_resp.json()
    assert len(hits) > 0
    assert "4 hours" in hits[0]["content"]
