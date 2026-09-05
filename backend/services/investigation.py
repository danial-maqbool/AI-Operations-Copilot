import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.services.warehouse import query_warehouse, get_warehouse_tables
from backend.services.rag_service import RAGService

class InvestigationEngine:
    @classmethod
    def investigate(
        cls,
        problem_description: str,
        workspace_id: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        prob_lower = problem_description.lower()
        tables = get_warehouse_tables()

        target_table = "orders"
        metric_col = "amount"
        group_candidates = []

        if "refund" in prob_lower or "return" in prob_lower:
            if "invoices" in tables:
                target_table = "invoices"
                metric_col = "unpaid_amount"
            elif "orders" in tables:
                target_table = "orders"
                metric_col = "amount"
        elif "delay" in prob_lower or "late" in prob_lower:
            target_table = "orders"
            metric_col = "order_id"
        elif "ticket" in prob_lower or "sla" in prob_lower:
            target_table = "support_tickets" if "support_tickets" in tables else "orders"
            metric_col = "ticket_id" if "support_tickets" in tables else "order_id"

        # Read target table
        try:
            df = query_warehouse(f'SELECT * FROM "{target_table}"')
        except Exception:
            return {
                "summary": f"Could not access operational data in '{target_table}' to investigate.",
                "drivers": [],
                "policy_context": None
            }

        if df.empty:
            return {
                "summary": f"Table '{target_table}' is empty, cannot compute root-cause attribution.",
                "drivers": [],
                "policy_context": None
            }

        # Identify candidate dimension columns (category, status, product, region, customer)
        cat_cols = [
            c for c in df.columns 
            if c not in [metric_col, "id", "created_at", "updated_at"]
            and (2 <= df[c].nunique() <= 20)
        ]

        # Calculate breakdown by top dimension
        drivers = []
        top_factor_pct = 0.0
        primary_dimension = None

        if cat_cols:
            primary_dimension = cat_cols[0]
            val_counts = df[primary_dimension].value_counts().head(3)
            total_items = len(df)
            
            for cat_val, count in val_counts.items():
                pct = round((count / total_items) * 100, 1)
                drivers.append({
                    "dimension": primary_dimension,
                    "segment": str(cat_val),
                    "volume": int(count),
                    "share_percentage": pct,
                    "explanation": f"Segment '{cat_val}' represents {count} records ({pct}% of total {target_table})"
                })
            top_factor_pct = sum(d["share_percentage"] for d in drivers)

        # Retrieve relevant policy if applicable
        policy_hits = RAGService.search(problem_description, workspace_id, db, top_k=1)
        policy_citation = policy_hits[0].citation if policy_hits else None
        policy_snippet = policy_hits[0].content[:200] + "..." if policy_hits else None

        # Compose evidence-backed summary
        summary = (
            f"Investigation into '{problem_description}':\n"
            f"Analyzed {len(df)} records in '{target_table}'. "
        )
        if primary_dimension and drivers:
            top_segs = ", ".join([f"{d['segment']} ({d['share_percentage']}%)" for d in drivers])
            summary += f"The leading operational driver across '{primary_dimension}' is concentrated in: {top_segs}. "
            summary += f"These key segments explain {top_factor_pct:.1f}% of volume."

        return {
            "target_table": target_table,
            "records_analyzed": len(df),
            "primary_dimension": primary_dimension,
            "drivers": drivers,
            "explained_share_percentage": round(top_factor_pct, 1),
            "summary": summary,
            "policy_citation": policy_citation,
            "policy_snippet": policy_snippet
        }
