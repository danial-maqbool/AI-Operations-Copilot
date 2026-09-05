import pytest
import pandas as pd
from backend.services.warehouse import query_warehouse
from backend.services.sql_safety import SafeSQLEngine

@pytest.fixture(scope="module", autouse=True)
def ensure_warehouse():
    # Make sure tables exist
    df = query_warehouse("SELECT count(*) as cnt FROM orders")
    assert df["cnt"].iloc[0] > 0

# Benchmark 1: Delayed Orders
def test_benchmark_01_delayed_orders():
    sql = "SELECT COUNT(*) as delayed_count FROM orders WHERE LOWER(status) = 'delayed'"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    count = int(df["delayed_count"].iloc[0])
    assert count > 0, "Should detect planted delayed orders"

# Benchmark 2: Total Revenue by Product Category
def test_benchmark_02_revenue_by_category():
    sql = """
        SELECT p.category, ROUND(SUM(oi.line_total), 2) as cat_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY cat_revenue DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 5
    assert df["cat_revenue"].sum() > 100000

# Benchmark 3: Overdue Invoices Total Exposure
def test_benchmark_03_overdue_invoices_exposure():
    sql = "SELECT ROUND(SUM(amount), 2) as total_overdue FROM invoices WHERE LOWER(status) = 'overdue'"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    overdue = float(df["total_overdue"].iloc[0])
    assert overdue > 0, "Should detect overdue accounts receivable"

# Benchmark 4: Products Below Reorder Level (Low Stock)
def test_benchmark_04_low_stock_products():
    sql = """
        SELECT sku, product_name, quantity_on_hand, reorder_level
        FROM inventory
        WHERE quantity_on_hand <= reorder_level
        ORDER BY quantity_on_hand ASC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 6, "Expected at least 6 low-stock planted items"

# Benchmark 5: Top 5 Customers by Order Spend
def test_benchmark_05_top_customers():
    sql = """
        SELECT c.customer_id, c.name, ROUND(SUM(o.total_amount), 2) as total_spent
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        ORDER BY total_spent DESC
        LIMIT 5
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) == 5
    assert df["total_spent"].iloc[0] >= df["total_spent"].iloc[4]

# Benchmark 6: Carriers with the Most Delayed Shipments
def test_benchmark_06_delayed_shipments_by_carrier():
    sql = """
        SELECT carrier, COUNT(*) as delay_count, ROUND(AVG(delay_days), 1) as avg_delay
        FROM shipments
        WHERE delay_days > 0
        GROUP BY carrier
        ORDER BY delay_count DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) > 0
    # Apex Logistics was planted with delays
    assert "Apex Logistics" in df["carrier"].values

# Benchmark 7: Support Ticket SLA Breach Rate
def test_benchmark_07_support_ticket_sla_breaches():
    sql = """
        SELECT 
            COUNT(*) as total_tickets,
            SUM(CASE WHEN LOWER(sla_status) = 'breached' THEN 1 ELSE 0 END) as breached_count,
            ROUND(AVG(CASE WHEN LOWER(sla_status) = 'breached' THEN 1.0 ELSE 0.0 END) * 100, 2) as breach_rate
        FROM support_tickets
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert int(df["breached_count"].iloc[0]) > 0
    assert float(df["breach_rate"].iloc[0]) > 0.0

# Benchmark 8: Customer Satisfaction by Priority
def test_benchmark_08_csat_by_priority():
    sql = """
        SELECT priority, ROUND(AVG(satisfaction_score), 2) as avg_csat
        FROM support_tickets
        WHERE satisfaction_score IS NOT NULL
        GROUP BY priority
        ORDER BY avg_csat ASC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 3

# Benchmark 9: Order Volume by Shipping Method
def test_benchmark_09_shipping_methods():
    sql = """
        SELECT shipping_method, COUNT(*) as order_count, ROUND(SUM(total_amount), 2) as total_val
        FROM orders
        GROUP BY shipping_method
        ORDER BY order_count DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 2

# Benchmark 10: Employees with Most Active Tasks
def test_benchmark_10_employee_workload():
    sql = """
        SELECT department, name, active_tasks
        FROM employees
        ORDER BY active_tasks DESC
        LIMIT 5
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) == 5
    assert df["active_tasks"].iloc[0] >= df["active_tasks"].iloc[4]

# Benchmark 11: Inventory Valuation by Warehouse
def test_benchmark_11_inventory_valuation():
    sql = """
        SELECT warehouse_location, ROUND(SUM(quantity_on_hand * unit_cost), 2) as total_valuation
        FROM inventory
        GROUP BY warehouse_location
        ORDER BY total_valuation DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) == 4
    assert df["total_valuation"].sum() > 50000

# Benchmark 12: Customers on Credit Hold
def test_benchmark_12_customers_on_credit_hold():
    sql = "SELECT customer_id, name, credit_limit, status FROM customers WHERE LOWER(status) = 'credit_hold'"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 1

# Benchmark 13: Average Order Value (AOV)
def test_benchmark_13_average_order_value():
    sql = "SELECT ROUND(AVG(total_amount), 2) as aov, COUNT(*) as total_orders FROM orders"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert float(df["aov"].iloc[0]) > 100.0
    assert int(df["total_orders"].iloc[0]) >= 1000

# Benchmark 14: Payment Methods Distribution
def test_benchmark_14_payment_methods():
    sql = """
        SELECT payment_method, COUNT(*) as pmt_count, ROUND(SUM(amount), 2) as total_collected
        FROM payments
        GROUP BY payment_method
        ORDER BY total_collected DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 2
    assert df["total_collected"].sum() > 10000

# Benchmark 15: Orders with Multiple Line Items
def test_benchmark_15_multiline_orders():
    sql = """
        SELECT order_id, COUNT(*) as item_count
        FROM order_items
        GROUP BY order_id
        HAVING COUNT(*) > 2
        LIMIT 10
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) > 0

# Benchmark 16: Customer Tiers Breakdown
def test_benchmark_16_customer_tiers():
    sql = """
        SELECT tier, COUNT(*) as cust_count, ROUND(AVG(credit_limit), 2) as avg_limit
        FROM customers
        GROUP BY tier
        ORDER BY cust_count DESC
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) >= 3

# Benchmark 17: Unique Products In Active Orders
def test_benchmark_17_unique_products_ordered():
    sql = "SELECT COUNT(DISTINCT product_id) as unique_prods FROM order_items"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert int(df["unique_prods"].iloc[0]) >= 50

# Benchmark 18: Unresolved Critical Support Tickets
def test_benchmark_18_unresolved_critical_tickets():
    sql = """
        SELECT ticket_id, subject, priority, status, sla_status
        FROM support_tickets
        WHERE priority = 'Critical' AND status != 'Resolved'
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) > 0

# Benchmark 19: Highest Value Products
def test_benchmark_19_highest_value_products():
    sql = "SELECT product_id, name, unit_price FROM products ORDER BY unit_price DESC LIMIT 3"
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) == 3
    assert df["unit_price"].iloc[0] > df["unit_price"].iloc[2]

# Benchmark 20: Delivery Timeliness by Month
def test_benchmark_20_delivery_timeliness():
    sql = """
        SELECT status, COUNT(*) as count
        FROM shipments
        GROUP BY status
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert "Delivered" in df["status"].values
    assert "Delayed" in df["status"].values

# Benchmark 21: Cross-Table Correlation (Orders vs Overdue Invoices)
def test_benchmark_21_cross_table_orders_invoices():
    sql = """
        SELECT c.name, COUNT(DISTINCT o.order_id) as total_orders, COUNT(DISTINCT i.invoice_id) as overdue_invoices
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN invoices i ON c.customer_id = i.customer_id AND LOWER(i.status) = 'overdue'
        GROUP BY c.name
        ORDER BY overdue_invoices DESC
        LIMIT 5
    """
    validated_sql, _ = SafeSQLEngine.validate_query(sql)
    df = query_warehouse(validated_sql)
    assert len(df) > 0
