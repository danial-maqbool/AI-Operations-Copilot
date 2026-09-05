import os
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from backend.database import SessionLocal, get_db
from backend.models.all_models import (
    Workspace, DataSource, DataSourceTable, Document
)
from backend.services.warehouse import WarehouseService, load_df_to_warehouse
from backend.services.profiler_service import ProfilerService
from backend.services.quality_service import QualityService
from backend.services.rag_service import RAGService
from backend.services.kpi_service import KPIService
from backend.services.rule_engine import RuleEngine

DEMO_DATA_DIR = os.path.join(os.getcwd(), "demo_data")
os.makedirs(DEMO_DATA_DIR, exist_ok=True)

class DemoSeedService:
    @staticmethod
    def generate_and_seed_demo_company(db: Session) -> dict:
        random.seed(42)  # Deterministic seed for reproducible benchmarks

        # 1. Get or create Workspace
        ws = db.query(Workspace).first()
        if not ws:
            ws = Workspace(name="Acme Industrial Supplies", description="Global B2B Operations & Logistics")
            db.add(ws)
            db.commit()
            db.refresh(ws)
        else:
            ws.name = "Acme Industrial Supplies"
            ws.description = "Global B2B Operations & Logistics"
            db.commit()

        base_date = datetime(2026, 8, 1)

        # 2. Generate Customers (120 customers)
        company_names = [
            "Apex Logistics", "Beacon Manufacturing", "Cascade Robotics", "Delta Heavy Industries",
            "Echo Medical Systems", "Falcon Energy", "Genesis Cloud", "Horizon Freight",
            "Ironclad Security", "Jupiter Dynamics", "Keystone Electronics", "Lighthouse Marine",
            "Monarch Aerospace", "Nexus Automation", "Omega Biotech", "Pinnacle Retail",
            "Quantum Optics", "Radiant Materials", "Summit Technologies", "Titan Mining",
            "Ultra Filtration", "Vanguard Defense", "Westlake Chemicals", "Xcel Engineering",
            "Zenith Power", "Borealis Sensors", "Crestview Labs", "DuraSteel Corp",
            "Evergreen Packaging", "Frontier Turbines"
        ]
        customers = []
        for i in range(1, 121):
            c_name = f"{company_names[(i - 1) % len(company_names)]} {((i - 1) // len(company_names)) + 1}"
            c_id = f"CUST-{1000 + i}"
            tier = random.choice(["Enterprise", "Mid-Market", "SMB", "Strategic"])
            limit = random.choice([25000, 50000, 100000, 250000, 500000])
            email = f"procurement@{c_name.lower().replace(' ', '')}.com"
            phone = f"+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
            city = random.choice(["Chicago", "Dallas", "Seattle", "Atlanta", "Denver", "Boston", "Phoenix", "Cleveland"])
            state = random.choice(["IL", "TX", "WA", "GA", "CO", "MA", "AZ", "OH"])
            customers.append({
                "customer_id": c_id,
                "name": c_name,
                "tier": tier,
                "credit_limit": limit,
                "email": email,
                "phone": phone,
                "city": city,
                "state": state,
                "status": "Active" if i != 14 else "Credit_Hold"
            })
        df_customers = pd.DataFrame(customers)
        df_customers.to_csv(os.path.join(DEMO_DATA_DIR, "customers.csv"), index=False)

        # 3. Generate Products (80 products)
        categories = ["Heavy Machinery", "Hydraulics", "Sensors & IoT", "Safety Equipment", "Fasteners", "Pneumatics"]
        products = []
        for i in range(1, 81):
            p_id = f"PROD-{200 + i}"
            cat = categories[i % len(categories)]
            cost = round(random.uniform(25.0, 450.0), 2)
            margin = random.uniform(1.35, 2.10)
            price = round(cost * margin, 2)
            reorder = random.choice([15, 25, 50, 100])
            name = f"{cat[:-1] if cat.endswith('s') else cat} Unit Mod-{100 + i}"
            products.append({
                "product_id": p_id,
                "name": name,
                "category": cat,
                "unit_cost": cost,
                "unit_price": price,
                "reorder_level": reorder
            })
        df_products = pd.DataFrame(products)
        df_products.to_csv(os.path.join(DEMO_DATA_DIR, "products.csv"), index=False)

        # 4. Generate Inventory (80 records with 6 low stock outliers)
        inventory = []
        warehouses = ["WH-East (NJ)", "WH-Central (IL)", "WH-West (NV)", "WH-South (TX)"]
        for p in products:
            sku = f"SKU-{p['product_id']}"
            reorder = p["reorder_level"]
            # Plant deliberate low-stock anomalies for 6 SKUs
            if p["product_id"] in ["PROD-205", "PROD-218", "PROD-233", "PROD-247", "PROD-260", "PROD-275"]:
                qty = random.randint(2, reorder - 1)
            else:
                qty = random.randint(reorder + 10, reorder * 6)
            
            inventory.append({
                "sku": sku,
                "product_id": p["product_id"],
                "product_name": p["name"],
                "warehouse_location": random.choice(warehouses),
                "quantity_on_hand": qty,
                "reorder_level": reorder,
                "safety_stock": int(reorder * 0.5),
                "unit_cost": p["unit_cost"]
            })
        df_inventory = pd.DataFrame(inventory)
        df_inventory.to_csv(os.path.join(DEMO_DATA_DIR, "inventory.csv"), index=False)

        # 5. Generate Orders & Order Items (1,200 orders, 3,000+ items)
        orders = []
        order_items = []
        shipments = []
        invoices = []
        payments = []

        carriers = ["FedEx Freight", "Apex Logistics", "Old Dominion", "UPS Freight", "Swift Transport"]
        item_counter = 1

        for i in range(1, 1201):
            o_id = f"ORD-{5000 + i}"
            cust = random.choice(customers)
            c_id = cust["customer_id"]
            
            # Days offset over last 45 days
            day_offset = random.randint(0, 42)
            o_date = base_date + timedelta(days=day_offset, hours=random.randint(8, 18))
            
            # 1 to 4 items per order
            n_items = random.randint(1, 4)
            order_total = 0.0

            for _ in range(n_items):
                prod = random.choice(products)
                qty = random.randint(1, 12)
                l_total = round(prod["unit_price"] * qty, 2)
                order_total += l_total
                order_items.append({
                    "item_id": f"ITEM-{item_counter}",
                    "order_id": o_id,
                    "product_id": prod["product_id"],
                    "quantity": qty,
                    "unit_price": prod["unit_price"],
                    "line_total": l_total
                })
                item_counter += 1

            # Plant status and deliberate delays
            # 12 orders are severely delayed (Apex Logistics regional issue)
            is_delayed = (i % 85 == 0) or (i in [42, 188, 305, 512, 730, 941])
            if is_delayed:
                status = "Delayed"
            elif day_offset >= 38:
                status = random.choice(["Processing", "Shipped"])
            else:
                status = "Delivered"

            orders.append({
                "order_id": o_id,
                "customer_id": c_id,
                "order_date": o_date.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "total_amount": round(order_total, 2),
                "shipping_method": "Ground Freight" if order_total < 5000 else "Expedited Air",
                "payment_terms": "Net 30"
            })

            # Shipments
            carrier = "Apex Logistics" if is_delayed else random.choice(carriers)
            ship_date = o_date + timedelta(days=1)
            est_del = ship_date + timedelta(days=3)
            delay_days = random.randint(5, 12) if is_delayed else (0 if status == "Delivered" else random.randint(0, 1))
            act_del = (est_del + timedelta(days=delay_days)) if status == "Delivered" or is_delayed else None

            shipments.append({
                "shipment_id": f"SHP-{8000 + i}",
                "order_id": o_id,
                "carrier": carrier,
                "tracking_number": f"TRK-{random.randint(10000000, 99999999)}",
                "ship_date": ship_date.strftime("%Y-%m-%d"),
                "estimated_delivery": est_del.strftime("%Y-%m-%d"),
                "actual_delivery": act_del.strftime("%Y-%m-%d") if act_del else None,
                "status": "Delayed" if is_delayed else ("Delivered" if status == "Delivered" else "In Transit"),
                "delay_days": delay_days
            })

            # Invoices
            inv_id = f"INV-{3000 + i}"
            due_date = o_date + timedelta(days=30)
            
            # Plant deliberate overdue invoices
            # Invoices older than 30 days that are unpaid
            is_overdue = (day_offset <= 10) and (i % 28 == 0 or i in [14, 56, 120, 240, 480])
            if is_overdue:
                inv_status = "Overdue"
            elif day_offset <= 12:
                inv_status = "Paid"
            else:
                inv_status = "Pending"

            invoices.append({
                "invoice_id": inv_id,
                "customer_id": c_id,
                "order_id": o_id,
                "issue_date": o_date.strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount": round(order_total, 2),
                "status": inv_status
            })

            # Payments for Paid invoices
            if inv_status == "Paid":
                payments.append({
                    "payment_id": f"PAY-{6000 + i}",
                    "invoice_id": inv_id,
                    "payment_date": (o_date + timedelta(days=random.randint(10, 28))).strftime("%Y-%m-%d"),
                    "amount": round(order_total, 2),
                    "payment_method": random.choice(["ACH Transfer", "Wire", "Corporate Card"]),
                    "reference": f"REF-{uuid.uuid4().hex[:8].upper()}"
                })

        df_orders = pd.DataFrame(orders)
        df_orders.to_csv(os.path.join(DEMO_DATA_DIR, "orders.csv"), index=False)

        df_items = pd.DataFrame(order_items)
        df_items.to_csv(os.path.join(DEMO_DATA_DIR, "order_items.csv"), index=False)

        df_shipments = pd.DataFrame(shipments)
        df_shipments.to_csv(os.path.join(DEMO_DATA_DIR, "shipments.csv"), index=False)

        df_invoices = pd.DataFrame(invoices)
        df_invoices.to_csv(os.path.join(DEMO_DATA_DIR, "invoices.csv"), index=False)

        df_payments = pd.DataFrame(payments)
        df_payments.to_csv(os.path.join(DEMO_DATA_DIR, "payments.csv"), index=False)

        # 6. Generate Support Tickets (320 tickets)
        tickets = []
        subjects = [
            "Delayed delivery status inquiry", "Invoice payment terms extension request",
            "Damaged package on delivery", "Incorrect SKU delivered in shipment",
            "Urgent quote for high-volume order", "Discrepancy on freight surcharge",
            "Request for Certificate of Conformance", "Order cancellation inquiry"
        ]
        for i in range(1, 321):
            t_id = f"TCK-{4000 + i}"
            c = random.choice(customers)
            subj = random.choice(subjects)
            prio = random.choice(["Low", "Medium", "High", "Critical"])
            
            # Plant deliberate SLA breaches on critical/high tickets
            is_breached = (prio in ["High", "Critical"]) and (i % 7 == 0)
            if is_breached:
                t_status = "In Progress"
                sla_st = "Breached"
            elif i % 5 == 0:
                t_status = "Waiting Customer"
                sla_st = "At Risk"
            else:
                t_status = "Resolved"
                sla_st = "Within SLA"

            created_dt = base_date + timedelta(days=random.randint(5, 40), hours=random.randint(8, 17))
            resolved_dt = (created_dt + timedelta(hours=random.randint(4, 72))) if t_status == "Resolved" else None

            tickets.append({
                "ticket_id": t_id,
                "customer_id": c["customer_id"],
                "subject": subj,
                "priority": prio,
                "status": t_status,
                "sla_status": sla_st,
                "created_at": created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_at": resolved_dt.strftime("%Y-%m-%d %H:%M:%S") if resolved_dt else None,
                "satisfaction_score": random.choice([4, 5, 5, 3, 4, 1 if is_breached else 5])
            })
        df_tickets = pd.DataFrame(tickets)
        df_tickets.to_csv(os.path.join(DEMO_DATA_DIR, "support_tickets.csv"), index=False)

        # 7. Generate Employees (50 records)
        depts = ["Fulfillment", "Customer Operations", "Finance & Billing", "Logistics", "Procurement"]
        employees = []
        emp_names = [
            "Sarah Jenkins", "Michael Chang", "Elena Rostova", "David Miller", "Amina Al-Mansoor",
            "Carlos Rodriguez", "Rachel Green", "James Wilson", "Priya Patel", "Thomas Mueller",
            "Grace Hopper", "Marcus Vance", "Olivia Taylor", "Liam Smith", "Sophia Lee",
            "Lucas Scott", "Isabella King", "Mason Wright", "Harper Hall", "Ethan Allen"
        ]
        for i in range(1, 51):
            e_name = f"{emp_names[(i - 1) % len(emp_names)]} {((i - 1) // len(emp_names)) + 1}"
            dept = depts[i % len(depts)]
            employees.append({
                "employee_id": f"EMP-{700 + i}",
                "name": e_name,
                "department": dept,
                "role": f"{dept} Specialist",
                "email": f"{e_name.lower().replace(' ', '.')}@acme.internal",
                "active_tasks": random.randint(2, 14),
                "resolved_tasks": random.randint(30, 180)
            })
        df_employees = pd.DataFrame(employees)
        df_employees.to_csv(os.path.join(DEMO_DATA_DIR, "employees.csv"), index=False)

        # 8. Load all tables into Operational Warehouse
        tables_to_load = [
            ("customers", df_customers),
            ("products", df_products),
            ("inventory", df_inventory),
            ("orders", df_orders),
            ("order_items", df_items),
            ("shipments", df_shipments),
            ("invoices", df_invoices),
            ("payments", df_payments),
            ("support_tickets", df_tickets),
            ("employees", df_employees)
        ]

        total_rows_loaded = 0
        for tbl_name, df in tables_to_load:
            load_df_to_warehouse(df, tbl_name, if_exists="replace")
            total_rows_loaded += len(df)

            # Register in Data Sources
            ds = db.query(DataSource).filter(DataSource.name == f"Demo {tbl_name.capitalize()}").first()
            if not ds:
                ds = DataSource(
                    workspace_id=ws.id,
                    name=f"Demo {tbl_name.capitalize()}",
                    source_type="csv",
                    file_path=os.path.join(DEMO_DATA_DIR, f"{tbl_name}.csv"),
                    status="connected",
                    row_count=len(df),
                    table_count=1
                )
                db.add(ds)
                db.commit()
                db.refresh(ds)
            else:
                ds.row_count = len(df)
                db.commit()

            # Register / update DataSourceTable
            dst = db.query(DataSourceTable).filter(DataSourceTable.table_name == tbl_name).first()
            if not dst:
                dst = DataSourceTable(
                    data_source_id=ds.id,
                    table_name=tbl_name,
                    row_count=len(df),
                    column_count=len(df.columns),
                    file_path=os.path.join(DEMO_DATA_DIR, f"{tbl_name}.csv")
                )
                db.add(dst)
                db.commit()
                db.refresh(dst)
            else:
                dst.row_count = len(df)
                dst.column_count = len(df.columns)
                db.commit()

            # Profile table & evaluate quality
            ProfilerService.profile_table(db, dst.id)
            QualityService.evaluate_table_quality(db, dst.id)

        # 9. Create and Ingest Operational Policy Documents into RAG
        policies = [
            {
                "filename": "Refund_and_Credit_Policy.md",
                "title": "Acme Industrial Customer Refund and Credit Note Policy",
                "content": """# Acme Industrial Supplies — Customer Refund & Credit Policy

## Section 1: Scope and Applicability
This standard operating procedure governs the issuance of monetary refunds, billing credits, and invoice adjustments for all B2B customer accounts.

## Section 2: Standard Refund Guidelines
- **Threshold for Operations Approval:** Refunds and credit notes below $5,000 may be approved directly by the Customer Operations Lead or Fulfillment Manager.
- **Executive Approval:** Credit adjustments or cash refunds exceeding $5,000 require explicit written authorization from the VP of Operations or Chief Financial Officer.
- **Filing Window:** Customers must report transit damage, shortages, or billing discrepancies within 14 calendar days of confirmed carrier delivery.

## Section 3: Damaged Goods and Carrier Fault
- In cases where delivery damage is attributable to the carrier (e.g. Apex Freight or FedEx), a carrier claim must be opened within 48 hours.
- A replacement order must be expedited immediately at zero additional cost to the customer if the customer tier is Enterprise or Strategic.
"""
            },
            {
                "filename": "Accounts_Receivable_SOP.md",
                "title": "Standard Operating Procedure — Accounts Receivable & Credit Hold",
                "content": """# Standard Operating Procedure — Accounts Receivable & Collections

## Section 1: Payment Terms & Escalation Timeline
- **Standard Terms:** All corporate invoices are Net 30 unless contractual agreements state Net 60.
- **Grace Period:** A 5-business-day grace period is allowed before automated late reminders are triggered.
- **15 Days Overdue:** The account manager is notified, and a formal payment request email is drafted.
- **30 Days Overdue:** The customer account is automatically placed on Credit Hold. Pending shipments are frozen until at least 50% of the past-due balance is settled.

## Section 2: Credit Hold Exceptions
Only the Chief Financial Officer may authorize an override to release shipments for accounts on Credit Hold.
"""
            },
            {
                "filename": "Customer_Support_SLA_Policy.md",
                "title": "Customer Support Operations SLA & Escalation Policy",
                "content": """# Customer Support Operations — Service Level Agreement Policy

## Section 1: Response and Resolution Time Targets
- **Critical Priority (Production Down / Missing Shipment):**
  - Initial Response Time: < 30 minutes.
  - Resolution Target: < 4 hours.
  - Escalation: Automatically escalates to Operations Lead if unassigned after 1 hour.
- **High Priority (Delayed Delivery / Damaged Goods):**
  - Initial Response Time: < 2 hours.
  - Resolution Target: < 24 hours.
- **Medium Priority (General Inquiry / Billing Question):**
  - Resolution Target: < 48 hours.
- **Low Priority:**
  - Resolution Target: < 5 business days.

## Section 2: SLA Breach Penalties
Any Enterprise account ticket exceeding resolution SLA targets by > 50% qualifies for a 5% credit on the associated shipment freight fee.
"""
            },
            {
                "filename": "Inventory_Reorder_and_Safety_Stock_Guidelines.md",
                "title": "Supply Chain & Warehouse Inventory Reorder Policy",
                "content": """# Warehouse Inventory & Safety Stock Policy

## Section 1: Safety Stock Formula
Safety stock is computed as:
Safety Stock = (Maximum Daily Usage * Maximum Lead Time Days) - (Average Daily Usage * Average Lead Time Days)

## Section 2: Mandatory Reorder Triggers
- When Quantity on Hand reaches or falls below the designated Reorder Level, the procurement system must trigger a Purchase Order draft.
- For Fast-Moving Category A SKUs (e.g. Sensors & Fasteners), stockouts must be reported to the Supply Chain Director within 24 hours.
"""
            }
        ]

        indexed_docs_count = 0
        for p in policies:
            filepath = os.path.join(DEMO_DATA_DIR, p["filename"])
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(p["content"])

            # Register document in DB
            from pathlib import Path
            RAGService.ingest_document(Path(filepath), p["filename"], ws.id, db)
            indexed_docs_count += 1

        # 10. Auto-seed KPIs and evaluate Business Rules
        KPIService.seed_defaults(ws.id, db)
        RuleEngine.evaluate_all_rules(ws.id, db)

        return {
            "status": "SUCCESS",
            "workspace_name": ws.name,
            "total_tables_loaded": len(tables_to_load),
            "total_rows_loaded": total_rows_loaded,
            "table_breakdown": {tbl: len(df) for tbl, df in tables_to_load},
            "documents_indexed": indexed_docs_count,
            "message": "Acme Industrial Supplies demo company successfully generated and loaded with realistic operational data, deliberate exceptions, and policy knowledge base."
        }
