import io
import json
import sqlite3
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ingest_csv(tmp_path):
    csv_file = tmp_path / "test_orders.csv"
    csv_file.write_text("order_id,customer_name,amount,status\n101,Acme Corp,1200.50,completed\n102,Globex,450.00,delayed", encoding="utf-8")
    
    with open(csv_file, "rb") as f:
        response = client.post("/api/data-sources/upload", files={"file": ("test_orders.csv", f, "text/csv")})
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_orders.csv"
    assert data["source_type"] == "csv"
    assert data["row_count"] == 2
    assert len(data["tables"]) == 1
    
    ds_id = data["id"]
    # Test preview
    tbl_name = data["tables"][0]["table_name"]
    prev_resp = client.get(f"/api/data-sources/{ds_id}/preview/{tbl_name}")
    assert prev_resp.status_code == 200
    p_data = prev_resp.json()
    assert len(p_data["rows"]) == 2
    assert p_data["rows"][0]["order_id"] == 101

def test_ingest_json(tmp_path):
    json_file = tmp_path / "test_inventory.json"
    records = [
        {"sku": "SKU-001", "name": "Widget A", "stock": 42},
        {"sku": "SKU-002", "name": "Widget B", "stock": 5}
    ]
    json_file.write_text(json.dumps(records), encoding="utf-8")
    
    with open(json_file, "rb") as f:
        response = client.post("/api/data-sources/upload", files={"file": ("test_inventory.json", f, "application/json")})
    
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "json"
    assert data["row_count"] == 2

def test_ingest_sqlite(tmp_path):
    db_file = tmp_path / "test_sqlite.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE products (product_id INT, name TEXT, price REAL)")
    cur.execute("INSERT INTO products VALUES (1, 'Widget', 19.99), (2, 'Gadget', 29.99)")
    conn.commit()
    conn.close()
    
    with open(db_file, "rb") as f:
        response = client.post("/api/data-sources/upload", files={"file": ("test_sqlite.db", f, "application/octet-stream")})
        
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "sqlite"
    assert data["row_count"] == 2
    assert data["table_count"] == 1

def test_postgres_credentials_masking():
    resp = client.post("/api/data-sources/postgres", json={
        "name": "Prod Postgres",
        "connection_uri": "postgresql://dbuser:supersecretpass@db.example.com:5432/ops"
    })
    assert resp.status_code == 200
    data = resp.json()
    # Password must NEVER be exposed
    assert "supersecretpass" not in data.get("connection_uri", "")
    assert "********" in data.get("connection_uri", "")
