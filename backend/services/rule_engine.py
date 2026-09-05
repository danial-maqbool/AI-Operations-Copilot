import re
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import BusinessRule, OperationsException, Workspace
from backend.services.warehouse import query_warehouse, get_warehouse_tables

DEFAULT_RULES = [
    {
        "name": "Overdue Invoices > ,000",
        "entity": "invoice",
        "target_table": "invoices",
        "severity": "CRITICAL",
        "conditions": [
            {"field": "unpaid_amount", "operator": "greater_than", "value": 5000},
            {"field": "status", "operator": "not_equals", "value": "paid"}
        ],
        "action_template": {"action_type": "create_task", "title": "Urgent collection follow-up"}
    },
    {
        "name": "Inventory Below Safety Stock",
        "entity": "inventory",
        "target_table": "inventory",
        "severity": "HIGH",
        "conditions": [
            {"field": "quantity_on_hand", "operator": "less_than_or_equal", "value": 20}
        ],
        "action_template": {"action_type": "create_task", "title": "Trigger supplier purchase order"}
    },
    {
        "name": "Delayed Order Fulfillment",
        "entity": "order",
        "target_table": "orders",
        "severity": "HIGH",
        "conditions": [
            {"field": "status", "operator": "equals", "value": "delayed"}
        ],
        "action_template": {"action_type": "draft_email", "title": "Notify customer regarding shipping delay"}
    },
    {
        "name": "SLA At-Risk Support Tickets",
        "entity": "ticket",
        "target_table": "support_tickets",
        "severity": "CRITICAL",
        "conditions": [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "status", "operator": "not_equals", "value": "resolved"}
        ],
        "action_template": {"action_type": "create_task", "title": "Escalate to tier-3 technical lead"}
    }
]

class BusinessRuleEngine:
    @classmethod
    def seed_default_rules(cls, workspace_id: str, db: Session):
        wh_tables = set(get_warehouse_tables())
        for r in DEFAULT_RULES:
            if r["target_table"] in wh_tables:
                existing = db.query(BusinessRule).filter(
                    BusinessRule.workspace_id == workspace_id,
                    BusinessRule.name == r["name"]
                ).first()
                if not existing:
                    new_rule = BusinessRule(
                        workspace_id=workspace_id,
                        name=r["name"],
                        entity=r["entity"],
                        target_table=r["target_table"],
                        severity=r["severity"],
                        conditions=r["conditions"],
                        action_template=r["action_template"],
                        is_active=True
                    )
                    db.add(new_rule)
        db.commit()

    @classmethod
    def evaluate_condition(cls, df: pd.DataFrame, cond: Dict[str, Any]) -> pd.Series:
        field = cond.get("field")
        op = cond.get("operator", "equals").lower()
        val = cond.get("value")

        if field not in df.columns:
            return pd.Series(False, index=df.index)

        series = df[field]

        if op in ["equals", "==", "eq"]:
            if pd.api.types.is_numeric_dtype(series.dtype):
                try:
                    return series == float(val)
                except Exception:
                    return series.astype(str) == str(val)
            return series.astype(str).str.lower() == str(val).lower()
        elif op in ["not_equals", "!=", "neq"]:
            if pd.api.types.is_numeric_dtype(series.dtype):
                try:
                    return series != float(val)
                except Exception:
                    return series.astype(str) != str(val)
            return series.astype(str).str.lower() != str(val).lower()
        elif op in ["greater_than", ">", "gt"]:
            return pd.to_numeric(series, errors="coerce") > float(val)
        elif op in ["less_than", "<", "lt"]:
            return pd.to_numeric(series, errors="coerce") < float(val)
        elif op in ["greater_than_or_equal", ">=", "gte"]:
            return pd.to_numeric(series, errors="coerce") >= float(val)
        elif op in ["less_than_or_equal", "<=", "lte"]:
            return pd.to_numeric(series, errors="coerce") <= float(val)
        elif op == "contains":
            return series.astype(str).str.lower().str.contains(str(val).lower(), na=False)
        elif op == "before":
            s_dt = pd.to_datetime(series, errors="coerce")
            v_dt = pd.to_datetime(val, errors="coerce")
            return s_dt < v_dt
        elif op == "after":
            s_dt = pd.to_datetime(series, errors="coerce")
            v_dt = pd.to_datetime(val, errors="coerce")
            return s_dt > v_dt
        elif op == "is_empty":
            return series.isnull() | (series.astype(str).str.strip() == "")
        elif op == "is_not_empty":
            return series.notnull() & (series.astype(str).str.strip() != "")
        else:
            return pd.Series(False, index=df.index)

    @classmethod
    def calculate_priority_score(
        cls,
        severity: str,
        financial_impact: float = 0.0,
        age_days: int = 0,
        sla_at_risk: bool = False
    ) -> float:
        # 1. Severity Points (Max 40)
        sev_map = {"CRITICAL": 40.0, "HIGH": 30.0, "WARNING": 25.0, "MEDIUM": 20.0, "LOW": 10.0, "INFO": 5.0}
        sev_pts = sev_map.get(severity.upper(), 20.0)

        # 2. Financial Impact Points (Max 25, linear up to ,000)
        fin_pts = min(25.0, (float(financial_impact) / 10000.0) * 25.0)

        # 3. Age Points (Max 20, linear up to 60 days)
        age_pts = min(20.0, (float(age_days) / 60.0) * 20.0)

        # 4. SLA Risk Points (Max 15)
        sla_pts = 15.0 if sla_at_risk else 0.0

        total = round(sev_pts + fin_pts + age_pts + sla_pts, 1)
        return min(100.0, max(0.0, total))

    @classmethod
    def evaluate_rule(cls, rule: BusinessRule, db: Session) -> List[OperationsException]:
        try:
            df = query_warehouse(f'SELECT * FROM "{rule.target_table}"')
        except Exception:
            return []

        if df.empty or not rule.conditions:
            return []

        # Combine conditions using logical AND
        combined_mask = pd.Series(True, index=df.index)
        for cond in rule.conditions:
            cond_mask = cls.evaluate_condition(df, cond)
            combined_mask = combined_mask & cond_mask

        matching_rows = df[combined_mask]
        if matching_rows.empty:
            return []

        # Find identifier column
        id_cols = [c for c in matching_rows.columns if c.endswith("_id") or c == "id" or c == "code" or c == "sku"]
        id_col = id_cols[0] if id_cols else matching_rows.columns[0]

        # Find amount / financial column
        amount_cols = [c for c in matching_rows.columns if any(kw in c.lower() for kw in ["amount", "balance", "price", "cost", "total"])]
        # Find date column for age calculation
        date_cols = [c for c in matching_rows.columns if any(kw in c.lower() for kw in ["date", "created_at", "due_date"])]

        exceptions_created = []

        for _, row in matching_rows.iterrows():
            entity_id = str(row[id_col])
            fin_val = float(row[amount_cols[0]]) if amount_cols and pd.notnull(row[amount_cols[0]]) and pd.api.types.is_numeric_dtype(type(row[amount_cols[0]])) else 0.0

            # Calculate age days
            age_days = 0
            if date_cols and pd.notnull(row[date_cols[0]]):
                try:
                    dt = pd.to_datetime(row[date_cols[0]])
                    age_days = max(0, (datetime.utcnow() - dt.to_pydatetime()).days)
                except Exception:
                    age_days = 0

            # Calculate Priority Score
            is_sla = "sla" in rule.target_table.lower() or "ticket" in rule.target_table.lower()
            priority_score = cls.calculate_priority_score(
                severity=rule.severity,
                financial_impact=fin_val,
                age_days=age_days,
                sla_at_risk=is_sla
            )

            title = f"{rule.name}: {rule.entity.capitalize()} #{entity_id}"
            if fin_val > 0:
                title += f" ()"

            # De-duplicate: check if exception already exists
            existing_exc = (
                db.query(OperationsException)
                .filter(
                    OperationsException.workspace_id == rule.workspace_id,
                    OperationsException.rule_id == rule.id,
                    OperationsException.entity_id == entity_id,
                    OperationsException.status.in_(["OPEN", "ACKNOWLEDGED"])
                )
                .first()
            )

            evidence_dict = {
                "rule_name": rule.name,
                "conditions_applied": rule.conditions,
                "record_data": {k: (float(v) if isinstance(v, (np.number, float)) else str(v)) for k, v in row.to_dict().items()}
            }

            if not existing_exc:
                exc = OperationsException(
                    workspace_id=rule.workspace_id,
                    rule_id=rule.id,
                    exception_type=rule.entity,
                    severity=rule.severity,
                    entity_type=rule.entity,
                    entity_id=entity_id,
                    title=title,
                    description=f"Triggered by rule '{rule.name}' on {rule.target_table}",
                    observed_value=str(row.get(rule.conditions[0]["field"], "")),
                    financial_impact=fin_val,
                    age_days=age_days,
                    priority_score=priority_score,
                    status="OPEN",
                    evidence=evidence_dict
                )
                db.add(exc)
                exceptions_created.append(exc)
            else:
                existing_exc.priority_score = priority_score
                existing_exc.evidence = evidence_dict
                exceptions_created.append(existing_exc)

        db.commit()
        return exceptions_created

    @classmethod
    def evaluate_all_rules(cls, workspace_id: Optional[str], db: Session) -> List[OperationsException]:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
        if not ws:
            return []

        # Seed defaults if needed
        cls.seed_default_rules(ws.id, db)

        rules = db.query(BusinessRule).filter(BusinessRule.workspace_id == ws.id, BusinessRule.is_active == True).all()
        all_exc = []
        for r in rules:
            all_exc.extend(cls.evaluate_rule(r, db))
        return all_exc
