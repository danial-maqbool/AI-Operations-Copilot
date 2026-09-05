import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.sql_safety import SQLSafetyValidator, SQLSafetyError
from backend.services.warehouse import load_df_to_warehouse
from backend.database import SessionLocal
from backend.models import AuditEvent

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_orders_table():
    df = pd.DataFrame({
        "order_id": [1, 2, 3, 4, 5],
        "customer_id": [101, 102, 101, 103, 102],
        "amount": [150.0, 200.0, 50.0, 300.0, 120.0],
        "status": ["delivered", "delayed", "delivered", "delayed", "pending"]
    })
    load_df_to_warehouse(df, "orders")

def test_safe_select_and_cte():
    # Standard SELECT
    res = SQLSafetyValidator.execute_safe_query("SELECT customer_id, COUNT(*) as cnt FROM orders GROUP BY customer_id")
    assert res["success"] is True
    assert len(res["rows"]) == 3
    assert "orders" in res["referenced_tables"]
    assert "customer_id" in res["columns"]
    assert res["explanation"] is not None

    # CTE query
    cte_sql = "WITH delayed_orders AS (SELECT * FROM orders WHERE status = 'delayed') SELECT * FROM delayed_orders"
    res_cte = SQLSafetyValidator.execute_safe_query(cte_sql)
    assert res_cte["success"] is True
    assert len(res_cte["rows"]) == 2
    # CTE alias 'delayed_orders' must not be flagged as external missing table
    assert "orders" in res_cte["referenced_tables"]

def test_enforce_limit():
    sql = "SELECT * FROM orders"
    sanitized, tables, explanation = SQLSafetyValidator.validate_and_sanitize(sql)
    assert "LIMIT 500" in sanitized

def test_block_write_queries():
    # DROP
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize("DROP TABLE orders")

    # DELETE
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize("DELETE FROM orders WHERE order_id = 1")

    # INSERT
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize("INSERT INTO orders (order_id) VALUES (99)")

    # UPDATE
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize("UPDATE orders SET status = 'cancelled'")

    # TRUNCATE
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize("TRUNCATE TABLE orders")

def test_block_multi_statement():
    multi = "SELECT * FROM orders; DROP TABLE orders;"
    with pytest.raises(SQLSafetyError):
        SQLSafetyValidator.validate_and_sanitize(multi)

def test_block_unregistered_table():
    with pytest.raises(SQLSafetyError) as exc_info:
        SQLSafetyValidator.validate_and_sanitize("SELECT * FROM non_existent_database_table")
    assert "does not exist" in str(exc_info.value)

def test_query_api_and_audit():
    resp = client.post("/api/queries/execute", json={"sql": "SELECT COUNT(*) as total_orders FROM orders"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["rows"][0]["total_orders"] == 5

    # Test rejection via API
    bad_resp = client.post("/api/queries/execute", json={"sql": "DELETE FROM orders"})
    assert bad_resp.status_code == 400
    assert "SQL Safety Violation" in bad_resp.json()["detail"]
