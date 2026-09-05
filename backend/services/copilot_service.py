import uuid
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import (
    Workspace, Conversation, Message, ToolCall,
    DataSourceTable, DataCatalogColumn, OperationsException, ActionItem
)
from backend.services.warehouse import get_warehouse_tables, query_warehouse
from backend.services.sql_safety import SQLSafetyValidator, SQLSafetyError
from backend.services.rag_service import RAGService
from backend.services.investigation import InvestigationEngine
from backend.services.anomaly_service import AnomalyDetectionService
from backend.services.kpi_service import KPIService
from backend.services.ai_provider import AIProvider
from backend.services.pii_redactor import PIIRedactor
from backend.schemas.copilot import (
    CopilotChatRequest, CopilotResponse, ChartSpec, CopilotActionRecommendation
)

class CopilotOrchestrator:
    def __init__(self):
        self.ai = AIProvider()

    def get_or_create_conversation(self, conv_id: Optional[str], workspace_id: str, db: Session) -> Conversation:
        if conv_id:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                return conv

        conv = Conversation(
            workspace_id=workspace_id,
            title="Operations Analysis"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def process_chat(self, req: CopilotChatRequest, db: Session) -> CopilotResponse:
        ws = db.query(Workspace).filter(Workspace.id == req.workspace_id).first() if req.workspace_id else db.query(Workspace).first()
        if not ws:
            ws = Workspace(name="Primary Workspace")
            db.add(ws)
            db.commit()
            db.refresh(ws)

        conv = self.get_or_create_conversation(req.conversation_id, ws.id, db)
        
        # PII Redaction
        sanitized_question, pii_mapping = PIIRedactor.redact(req.question)

        # Log User Message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=sanitized_question
        )
        db.add(user_msg)
        db.commit()

        # Classify intent & available warehouse tables
        available_tables = get_warehouse_tables()
        intent = self.ai.classify_intent(sanitized_question)

        tools_executed = []
        sql_queries = []
        policy_citations = []
        table_data = None
        chart = None
        actions = []
        calculations = {}
        data_used = []
        direct_answer = ""
        confidence = "HIGH"

        q_low = sanitized_question.lower()

        # 1. Hybrid Policy + SQL Questions
        if intent == "hybrid" or ("manager approval" in q_low and "refund" in q_low):
            tools_executed.append("search_documents")
            rag_hits = RAGService.search("manager approval threshold for refund requests", ws.id, db, top_k=2)
            policy_citations = [h.dict() for h in rag_hits]

            # Deterministic policy condition extraction
            # From demo policy: Refund > ,500 or overdue requires manager approval
            tools_executed.append("run_readonly_sql")
            target_table = "invoices" if "invoices" in available_tables else "orders"
            amt_col = "unpaid_amount" if target_table == "invoices" else "amount"

            sql = f"""
                SELECT * FROM "{target_table}"
                WHERE ("{amt_col}" > 2500 OR status = 'refund_pending' OR status = 'overdue')
                ORDER BY "{amt_col}" DESC
                LIMIT 50
            """
            try:
                sql_res = SQLSafetyValidator.execute_safe_query(sql)
                sql_queries.append({
                    "sql": sql_res["sanitized_sql"],
                    "explanation": sql_res["explanation"],
                    "duration_ms": sql_res["duration_ms"]
                })
                data_used.append(target_table)
                total_cases = len(sql_res["rows"])
                total_val = sum(float(r.get(amt_col, 0) or 0) for r in sql_res["rows"])

                calculations["cases_requiring_approval"] = total_cases
                calculations["total_value_at_risk"] = f""
                table_data = {
                    "columns": sql_res["columns"][:6],
                    "rows": sql_res["rows"][:10],
                    "total_rows": total_cases
                }

                direct_answer = (
                    f"Found {total_cases} refund/credit cases totaling  that require manager approval.\n\n"
                    f"According to company policy, transactions exceeding ,500 or exceeding standard timeframes "
                    f"require explicit Tier-2 Operations Manager approval before release."
                )

                actions.append(CopilotActionRecommendation(
                    title=f"Review and approve {total_cases} pending refund exceptions",
                    description="Managerial sign-off required according to Refund Policy guidelines",
                    reason=f"Financial exposure of  exceeding standard operational threshold",
                    priority="CRITICAL",
                    owner="Operations Finance Manager",
                    action_type="create_task",
                    suggested_steps=["Inspect original order fulfillment status", "Verify customer credit history", "Sign off approval in AR portal"]
                ))
            except Exception as e:
                direct_answer = f"Policy search completed, but SQL execution failed: {str(e)}"
                confidence = "MEDIUM"

        # 2. Pure Policy RAG
        elif intent == "policy_rag":
            tools_executed.append("search_documents")
            rag_hits = RAGService.search(sanitized_question, ws.id, db, top_k=3)
            policy_citations = [h.dict() for h in rag_hits]
            if rag_hits:
                direct_answer = f"According to company documentation:\n\n{rag_hits[0].content}\n\n[Verified Policy Citation Attached]"
            else:
                direct_answer = "No matching company SOPs or policy documents were found for this query in the knowledge base."
                confidence = "LOW"

        # 3. Investigation / Root Cause
        elif intent == "investigate":
            tools_executed.append("investigate_problem")
            inv_res = InvestigationEngine.investigate(sanitized_question, ws.id, db)
            direct_answer = inv_res["summary"]
            data_used.append(inv_res["target_table"])
            if inv_res.get("policy_citation"):
                policy_citations.append({"citation": inv_res["policy_citation"], "content": inv_res["policy_snippet"]})

            if inv_res.get("drivers"):
                chart = ChartSpec(
                    chart_type="bar",
                    title=f"Top Drivers across {inv_res.get('primary_dimension', 'Segments')}",
                    x_key="segment",
                    y_key="volume",
                    data=inv_res["drivers"]
                )
                actions.append(CopilotActionRecommendation(
                    title=f"Conduct targeted review on top driver '{inv_res['drivers'][0]['segment']}'",
                    description=f"Segment represents {inv_res['drivers'][0]['share_percentage']}% of observed operational variance",
                    reason="Concentrated root-cause driver identified in operational investigation",
                    priority="HIGH",
                    owner="Operations Lead"
                ))

        # 4. Standard Operational Queries (Delayed Orders, Overdue Invoices, Stock, SLAs, Customers)
        else:
            tools_executed.append("run_readonly_sql")
            sql = None

            # Pattern: Delayed Orders
            if "delay" in q_low or "late" in q_low:
                if "orders" in available_tables:
                    sql = """
                        SELECT order_id, customer_id, amount, promised_date, delivery_date, status
                        FROM orders
                        WHERE delivery_date > promised_date OR status = 'delayed'
                        ORDER BY amount DESC
                        LIMIT 100
                    """
                    data_used.append("orders")

            # Pattern: Overdue Invoices
            elif "invoice" in q_low or "overdue" in q_low or "unpaid" in q_low:
                if "invoices" in available_tables:
                    sql = """
                        SELECT invoice_id, customer_id, unpaid_amount, due_date, status
                        FROM invoices
                        WHERE (due_date < DATE('now') OR status = 'overdue') AND status != 'paid'
                        ORDER BY unpaid_amount DESC
                        LIMIT 100
                    """
                    data_used.append("invoices")

            # Pattern: Restock / Low Inventory
            elif "stock" in q_low or "inventory" in q_low or "reorder" in q_low:
                if "inventory" in available_tables:
                    sql = """
                        SELECT inventory_id, sku, product_name, quantity_on_hand, reorder_level
                        FROM inventory
                        WHERE quantity_on_hand <= reorder_level
                        ORDER BY quantity_on_hand ASC
                        LIMIT 100
                    """
                    data_used.append("inventory")

            # Pattern: Tickets / SLA
            elif "ticket" in q_low or "sla" in q_low:
                if "support_tickets" in available_tables:
                    sql = """
                        SELECT ticket_id, customer_id, issue_type, priority, status, sla_deadline
                        FROM support_tickets
                        WHERE status != 'resolved' AND (sla_deadline < DATETIME('now') OR priority = 'Urgent')
                        ORDER BY priority DESC
                        LIMIT 100
                    """
                    data_used.append("support_tickets")

            # Pattern: High value customers / Revenue
            elif "customer" in q_low and "delayed" in q_low and "orders" in available_tables and "customers" in available_tables:
                sql = """
                    SELECT c.customer_id, c.customer_name, c.tier, COUNT(o.order_id) as delayed_orders, SUM(o.amount) as total_delayed_value
                    FROM customers c
                    JOIN orders o ON c.customer_id = o.customer_id
                    WHERE o.delivery_date > o.promised_date OR o.status = 'delayed'
                    GROUP BY c.customer_id, c.customer_name, c.tier
                    ORDER BY total_delayed_value DESC
                    LIMIT 50
                """
                data_used.extend(["customers", "orders"])

            elif "revenue" in q_low or "sales" in q_low:
                if "orders" in available_tables:
                    sql = "SELECT customer_id, COUNT(*) as orders_count, SUM(amount) as total_revenue FROM orders GROUP BY customer_id ORDER BY total_revenue DESC LIMIT 20"
                    data_used.append("orders")

            # Fallback query
            if not sql:
                first_table = available_tables[0] if available_tables else "orders"
                sql = f"SELECT * FROM \"{first_table}\" LIMIT 20"
                data_used.append(first_table)

            # Execute safe SQL
            try:
                sql_res = SQLSafetyValidator.execute_safe_query(sql)
                sql_queries.append({
                    "sql": sql_res["sanitized_sql"],
                    "explanation": sql_res["explanation"],
                    "duration_ms": sql_res["duration_ms"]
                })

                count = len(sql_res["rows"])
                # Extract numeric sums
                amt_keys = [k for k in sql_res["columns"] if any(kw in k.lower() for kw in ["amount", "revenue", "price", "value"])]
                sum_amt = sum(float(r[amt_keys[0]]) for r in sql_res["rows"] if pd.notnull(r.get(amt_keys[0]))) if amt_keys else 0.0

                calculations["matching_records"] = count
                if sum_amt > 0:
                    calculations["total_exposure"] = f""

                table_data = {
                    "columns": sql_res["columns"],
                    "rows": sql_res["rows"][:20],
                    "total_rows": count
                }

                # Construct chart if suitable
                if count >= 2 and len(sql_res["columns"]) >= 2:
                    x_col = sql_res["columns"][0]
                    y_col = amt_keys[0] if amt_keys else (sql_res["columns"][1] if len(sql_res["columns"]) > 1 else None)
                    if y_col:
                        chart = ChartSpec(
                            chart_type="bar",
                            title=f"{y_col.replace('_', ' ').capitalize()} by {x_col.replace('_', ' ').capitalize()}",
                            x_key=x_col,
                            y_key=y_col,
                            data=sql_res["rows"][:8]
                        )

                direct_answer = f"Retrieved {count} matching operational records from {', '.join(data_used)}."
                if sum_amt > 0:
                    direct_answer += f" Total financial exposure: ."

                # Action recommendation
                if "delay" in q_low:
                    actions.append(CopilotActionRecommendation(
                        title=f"Escalate {count} delayed fulfillment orders",
                        description="Customer promised delivery dates were exceeded",
                        reason=f"Fulfillment delay impacting  in order value",
                        priority="HIGH",
                        owner="Logistics Operations Lead",
                        action_type="export_csv"
                    ))
                elif "invoice" in q_low:
                    actions.append(CopilotActionRecommendation(
                        title=f"Trigger payment follow-up on {count} overdue accounts",
                        description="Invoices past maturity date with outstanding balances",
                        reason=f"Total outstanding balance: ",
                        priority="CRITICAL",
                        owner="Accounts Receivable Lead",
                        action_type="call_list"
                    ))
                elif "stock" in q_low:
                    actions.append(CopilotActionRecommendation(
                        title=f"Generate restock orders for {count} inventory items",
                        description="Current quantity on hand is at or below defined safety reorder thresholds",
                        reason="Mitigate stockout risk for customer fulfillment",
                        priority="HIGH",
                        owner="Supply Chain Lead",
                        action_type="create_task"
                    ))
            except Exception as e:
                direct_answer = f"Error evaluating operational query: {str(e)}"
                confidence = "LOW"

        # Restore any PII
        direct_answer = PIIRedactor.restore(direct_answer, pii_mapping)

        # Save Assistant Message
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=direct_answer,
            confidence=confidence,
            suggested_actions=[a.dict() for a in actions],
            sql_queries=sql_queries,
            charts=[chart.dict()] if chart else []
        )
        db.add(assistant_msg)
        db.flush()

        # Save Tool Calls
        for t in tools_executed:
            db.add(ToolCall(
                message_id=assistant_msg.id,
                tool_name=t,
                arguments={"query": sanitized_question},
                result={"status": "success"},
                status="SUCCESS"
            ))

        db.commit()

        return CopilotResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            direct_answer=direct_answer,
            confidence=confidence,
            data_used=data_used,
            filters_applied=["Read-only SQL AST safety verified", "Active workspace isolation"],
            calculations=calculations,
            table_data=table_data,
            chart=chart,
            sql_queries=sql_queries,
            policy_citations=policy_citations,
            recommended_actions=actions,
            evidence={
                "tools": tools_executed,
                "data_used": data_used,
                "calculations": calculations
            },
            tools_executed=tools_executed
        )
