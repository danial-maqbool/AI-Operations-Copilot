import pytest
from backend.database import SessionLocal, init_db
from backend.services.copilot_service import OperationsCopilot

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_hybrid_benchmark_01_credit_hold_policy_and_database(db):
    question = "Which customers have overdue invoices and should be subject to Credit Hold under our AR policy?"
    response = OperationsCopilot.process_user_turn(
        question=question,
        conversation_id=None,
        workspace_id=None,
        db=db
    )
    assert response is not None
    assert len(response.answer) > 20
    # Must have both document citations and SQL execution or structured findings
    assert len(response.document_citations) > 0 or "Accounts_Receivable" in str(response.tool_calls_executed)
    assert len(response.sql_queries) > 0 or len(response.tool_calls_executed) > 0

def test_hybrid_benchmark_02_refund_approval_policy_and_amounts(db):
    question = "What is the policy threshold for refund approvals, and which recent orders have total amount greater than 5000?"
    response = OperationsCopilot.process_user_turn(
        question=question,
        conversation_id=None,
        workspace_id=None,
        db=db
    )
    assert response is not None
    assert len(response.answer) > 20
    assert len(response.document_citations) > 0 or "Refund_and_Credit_Policy" in str(response.tool_calls_executed)
