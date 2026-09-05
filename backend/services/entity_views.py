import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.services.warehouse import WarehouseService

class EntityViewService:
    @staticmethod
    def get_customer_360(customer_id: str) -> Dict[str, Any]:
        """
        Aggregates comprehensive operational profile for a customer across:
        - Customers table
        - Orders table
        - Invoices table
        - Support tickets table
        """
        engine = WarehouseService.get_engine()
        
        # 1. Customer record
        customer_info = {}
        try:
            df_cust = pd.read_sql_query(
                "SELECT * FROM customers WHERE LOWER(customer_id) = LOWER(?) OR LOWER(name) LIKE LOWER(?) LIMIT 1",
                engine,
                params=[customer_id, f"%{customer_id}%"]
            )
            if not df_cust.empty:
                customer_info = df_cust.to_dict(orient="records")[0]
                matched_id = customer_info.get("customer_id", customer_id)
            else:
                matched_id = customer_id
        except Exception:
            matched_id = customer_id

        # 2. Orders
        orders = []
        total_spent = 0.0
        late_orders_count = 0
        try:
            df_orders = pd.read_sql_query(
                "SELECT * FROM orders WHERE LOWER(customer_id) = LOWER(?) ORDER BY order_date DESC LIMIT 50",
                engine,
                params=[matched_id]
            )
            if not df_orders.empty:
                orders = df_orders.to_dict(orient="records")
                if "total_amount" in df_orders.columns:
                    total_spent = float(pd.to_numeric(df_orders["total_amount"], errors="coerce").fillna(0).sum())
                
                # Check status
                if "status" in df_orders.columns:
                    late_orders_count = int(df_orders["status"].astype(str).str.lower().str.contains("delay|late").sum())
        except Exception:
            pass

        # 3. Invoices
        invoices = []
        open_balance = 0.0
        overdue_invoices_count = 0
        try:
            df_inv = pd.read_sql_query(
                "SELECT * FROM invoices WHERE LOWER(customer_id) = LOWER(?) ORDER BY due_date DESC LIMIT 50",
                engine,
                params=[matched_id]
            )
            if not df_inv.empty:
                invoices = df_inv.to_dict(orient="records")
                # compute overdue
                if "amount" in df_inv.columns and "status" in df_inv.columns:
                    unpaid_mask = ~df_inv["status"].astype(str).str.lower().isin(["paid", "settled", "void"])
                    open_balance = float(pd.to_numeric(df_inv.loc[unpaid_mask, "amount"], errors="coerce").fillna(0).sum())
                    overdue_mask = unpaid_mask & (df_inv["status"].astype(str).str.lower().str.contains("overdue"))
                    overdue_invoices_count = int(overdue_mask.sum())
        except Exception:
            pass

        # 4. Support Tickets
        tickets = []
        open_tickets_count = 0
        breached_tickets_count = 0
        try:
            df_tickets = pd.read_sql_query(
                "SELECT * FROM support_tickets WHERE LOWER(customer_id) = LOWER(?) ORDER BY created_at DESC LIMIT 50",
                engine,
                params=[matched_id]
            )
            if not df_tickets.empty:
                tickets = df_tickets.to_dict(orient="records")
                if "status" in df_tickets.columns:
                    open_mask = ~df_tickets["status"].astype(str).str.lower().isin(["closed", "resolved"])
                    open_tickets_count = int(open_mask.sum())
                if "sla_status" in df_tickets.columns:
                    breached_tickets_count = int(df_tickets["sla_status"].astype(str).str.lower().str.contains("breach").sum())
        except Exception:
            pass

        # 5. Compute Customer Health / Risk Score
        # Max score: 100
        penalties = (overdue_invoices_count * 20.0) + (late_orders_count * 15.0) + (open_tickets_count * 10.0) + (breached_tickets_count * 25.0)
        if open_balance > 1000.0:
            penalties += 15.0
        
        health_score = max(0.0, min(100.0, round(100.0 - penalties, 1)))
        if health_score >= 80:
            risk_tier = "LOW_RISK"
        elif health_score >= 50:
            risk_tier = "MEDIUM_RISK"
        else:
            risk_tier = "HIGH_RISK"

        return {
            "customer_id": matched_id,
            "profile": customer_info or {"customer_id": matched_id, "name": "Unknown Customer"},
            "metrics": {
                "health_score": health_score,
                "risk_tier": risk_tier,
                "total_orders": len(orders),
                "total_spent": round(total_spent, 2),
                "late_orders": late_orders_count,
                "open_invoices_balance": round(open_balance, 2),
                "overdue_invoices": overdue_invoices_count,
                "open_tickets": open_tickets_count,
                "breached_tickets": breached_tickets_count
            },
            "orders": orders[:10],
            "invoices": invoices[:10],
            "support_tickets": tickets[:10],
            "recommended_actions": [
                f"Contact customer regarding ${open_balance:,.2f} open balance" if open_balance > 0 else "Account in good billing standing",
                f"Escalate {open_tickets_count} unresolved support tickets" if open_tickets_count > 0 else "No open support escalations"
            ]
        }

    @staticmethod
    def get_order_360(order_id: str) -> Dict[str, Any]:
        """
        Aggregates complete trace of an order:
        - Order header
        - Order items / products
        - Shipment & carrier tracking
        - Invoice & payment status
        - SLA timeliness evaluation
        """
        engine = WarehouseService.get_engine()

        order_data = {}
        items = []
        shipments = []
        invoices = []

        try:
            df_order = pd.read_sql_query(
                "SELECT * FROM orders WHERE LOWER(order_id) = LOWER(?) LIMIT 1",
                engine,
                params=[order_id]
            )
            if not df_order.empty:
                order_data = df_order.to_dict(orient="records")[0]
        except Exception:
            pass

        # Items
        try:
            df_items = pd.read_sql_query(
                "SELECT * FROM order_items WHERE LOWER(order_id) = LOWER(?)",
                engine,
                params=[order_id]
            )
            if not df_items.empty:
                items = df_items.to_dict(orient="records")
        except Exception:
            pass

        # Shipments
        try:
            df_ship = pd.read_sql_query(
                "SELECT * FROM shipments WHERE LOWER(order_id) = LOWER(?)",
                engine,
                params=[order_id]
            )
            if not df_ship.empty:
                shipments = df_ship.to_dict(orient="records")
        except Exception:
            pass

        # Invoices
        try:
            df_inv = pd.read_sql_query(
                "SELECT * FROM invoices WHERE LOWER(order_id) = LOWER(?)",
                engine,
                params=[order_id]
            )
            if not df_inv.empty:
                invoices = df_inv.to_dict(orient="records")
        except Exception:
            pass

        # SLA analysis
        sla_status = "ON_TIME"
        delay_days = 0
        status_str = str(order_data.get("status", "")).lower()
        if "delay" in status_str or "late" in status_str:
            sla_status = "DELAYED"
            delay_days = 3
        elif shipments:
            s_status = str(shipments[0].get("status", "")).lower()
            if "delay" in s_status:
                sla_status = "DELAYED"
                delay_days = int(shipments[0].get("delay_days", 2))

        return {
            "order_id": order_id,
            "order": order_data or {"order_id": order_id, "status": "NOT_FOUND"},
            "items": items,
            "shipments": shipments,
            "invoices": invoices,
            "sla": {
                "status": sla_status,
                "delay_days": delay_days,
                "carrier": shipments[0].get("carrier", "N/A") if shipments else "N/A",
                "tracking_number": shipments[0].get("tracking_number", "N/A") if shipments else "N/A"
            }
        }

    @staticmethod
    def get_sla_risk_monitor() -> Dict[str, Any]:
        """
        Global operational SLA risk monitor scanning orders, support tickets, and shipments.
        Returns:
        - summary (breached, at_risk, safe, financial_exposure)
        - breached_items
        - at_risk_items
        """
        engine = WarehouseService.get_engine()
        breached_items: List[Dict[str, Any]] = []
        at_risk_items: List[Dict[str, Any]] = []
        total_monitored = 0
        total_exposure = 0.0

        # 1. Orders SLA
        try:
            df_orders = pd.read_sql_query("SELECT * FROM orders", engine)
            if not df_orders.empty:
                total_monitored += len(df_orders)
                for _, row in df_orders.iterrows():
                    st = str(row.get("status", "")).lower()
                    amt = float(pd.to_numeric(pd.Series([row.get("total_amount", 0)]), errors="coerce").fillna(0).iloc[0])
                    if "delay" in st or "late" in st:
                        breached_items.append({
                            "entity_type": "order",
                            "entity_id": str(row.get("order_id", "")),
                            "customer_id": str(row.get("customer_id", "")),
                            "title": f"Order {row.get('order_id')} is Delayed",
                            "severity": "CRITICAL",
                            "status": "BREACHED",
                            "financial_impact": amt,
                            "sla_type": "Delivery SLA",
                            "details": f"Status: {row.get('status')}, Order Date: {row.get('order_date')}"
                        })
                        total_exposure += amt
                    elif "pending" in st or "processing" in st:
                        at_risk_items.append({
                            "entity_type": "order",
                            "entity_id": str(row.get("order_id", "")),
                            "customer_id": str(row.get("customer_id", "")),
                            "title": f"Order {row.get('order_id')} in Processing",
                            "severity": "WARNING",
                            "status": "AT_RISK",
                            "financial_impact": amt,
                            "sla_type": "Fulfillment SLA",
                            "details": f"Pending fulfillment since {row.get('order_date')}"
                        })
        except Exception:
            pass

        # 2. Support Tickets SLA
        try:
            df_tickets = pd.read_sql_query("SELECT * FROM support_tickets", engine)
            if not df_tickets.empty:
                total_monitored += len(df_tickets)
                for _, row in df_tickets.iterrows():
                    sla_st = str(row.get("sla_status", "")).lower()
                    st = str(row.get("status", "")).lower()
                    prio = str(row.get("priority", "MEDIUM")).upper()
                    
                    if "breach" in sla_st or "breached" in sla_st:
                        breached_items.append({
                            "entity_type": "ticket",
                            "entity_id": str(row.get("ticket_id", "")),
                            "customer_id": str(row.get("customer_id", "")),
                            "title": f"Ticket #{row.get('ticket_id')} - {row.get('subject', 'Customer Issue')}",
                            "severity": "CRITICAL",
                            "status": "BREACHED",
                            "financial_impact": 500.0 if prio == "CRITICAL" else 200.0,
                            "sla_type": "Support Response SLA",
                            "details": f"Priority: {prio}, SLA Status: Breached"
                        })
                        total_exposure += 500.0 if prio == "CRITICAL" else 200.0
                    elif "at_risk" in sla_st or (st not in ["closed", "resolved"] and prio in ["HIGH", "CRITICAL"]):
                        at_risk_items.append({
                            "entity_type": "ticket",
                            "entity_id": str(row.get("ticket_id", "")),
                            "customer_id": str(row.get("customer_id", "")),
                            "title": f"Ticket #{row.get('ticket_id')} Approaching SLA Breach",
                            "severity": "WARNING",
                            "status": "AT_RISK",
                            "financial_impact": 200.0,
                            "sla_type": "Support Response SLA",
                            "details": f"Priority: {prio}, Resolution due shortly"
                        })
        except Exception:
            pass

        # 3. Overdue Invoices
        try:
            df_inv = pd.read_sql_query("SELECT * FROM invoices", engine)
            if not df_inv.empty:
                total_monitored += len(df_inv)
                for _, row in df_inv.iterrows():
                    st = str(row.get("status", "")).lower()
                    amt = float(pd.to_numeric(pd.Series([row.get("amount", 0)]), errors="coerce").fillna(0).iloc[0])
                    if "overdue" in st:
                        breached_items.append({
                            "entity_type": "invoice",
                            "entity_id": str(row.get("invoice_id", "")),
                            "customer_id": str(row.get("customer_id", "")),
                            "title": f"Invoice {row.get('invoice_id')} Overdue",
                            "severity": "HIGH",
                            "status": "BREACHED",
                            "financial_impact": amt,
                            "sla_type": "Payment Terms SLA",
                            "details": f"Due Date: {row.get('due_date')}, Overdue balance: ${amt:,.2f}"
                        })
                        total_exposure += amt
        except Exception:
            pass

        return {
            "summary": {
                "total_monitored": total_monitored,
                "breached_count": len(breached_items),
                "at_risk_count": len(at_risk_items),
                "safe_count": max(0, total_monitored - len(breached_items) - len(at_risk_items)),
                "financial_exposure": round(total_exposure, 2),
                "updated_at": datetime.utcnow().isoformat()
            },
            "breached": breached_items[:30],
            "at_risk": at_risk_items[:30]
        }
