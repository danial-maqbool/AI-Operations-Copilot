import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.models.all_models import (
    Workflow, WorkflowRun, Workspace, DataSourceTable,
    OperationsException, ActionItem, AuditEvent
)
from backend.services.kpi_service import KPIService
from backend.services.rule_engine import RuleEngine
from backend.services.anomaly_service import AnomalyService
from backend.services.entity_views import EntityViewService
from backend.services.warehouse import WarehouseService
from backend.services.ai_provider import AIProvider

class MorningReviewService:
    @staticmethod
    def get_or_create_morning_workflow(db: Session, workspace_id: str) -> Workflow:
        wf = db.query(Workflow).filter(Workflow.name == "Morning Operations Routine").first()
        if not wf:
            wf = Workflow(
                workspace_id=workspace_id,
                name="Morning Operations Routine",
                description="Automated comprehensive daily operations health audit, KPI sync, SLA evaluation, and priority action formulation.",
                trigger_type="schedule",
                steps=[
                    {"step_id": "s1", "name": "Sync Operations KPIs", "step_type": "calculate_kpis"},
                    {"step_id": "s2", "name": "Evaluate Business Rules", "step_type": "evaluate_rules"},
                    {"step_id": "s3", "name": "Scan SLA Breaches", "step_type": "check_sla_breaches"},
                    {"step_id": "s4", "name": "Detect Operational Outliers", "step_type": "detect_anomalies"},
                    {"step_id": "s5", "name": "Generate Priority Action Plan", "step_type": "generate_action_plan"}
                ],
                is_active=True
            )
            db.add(wf)
            db.commit()
            db.refresh(wf)
        return wf

    @staticmethod
    def run_morning_review(db: Session) -> Dict[str, Any]:
        start_time = time.time()
        review_id = f"REV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 1. Ensure Workspace
        ws = db.query(Workspace).first()
        if not ws:
            ws = Workspace(name="Default Workspace")
            db.add(ws)
            db.commit()
            db.refresh(ws)
        workspace_id = ws.id

        workflow = MorningReviewService.get_or_create_morning_workflow(db, workspace_id)

        # 2. Data Health Score
        tables = db.query(DataSourceTable).all()
        if tables:
            avg_health = round(sum(t.data_health_score or 100.0 for t in tables) / len(tables), 1)
        else:
            avg_health = 100.0

        # 3. KPI Summary
        kpis = KPIService.get_all_kpi_snapshots(db)
        kpi_counts = {"GOOD": 0, "WARNING": 0, "CRITICAL": 0}
        for k in kpis:
            kpi_counts[k.get("status", "GOOD")] = kpi_counts.get(k.get("status", "GOOD"), 0) + 1

        # 4. Rules & Exceptions
        exceptions = RuleEngine.evaluate_all_rules(db)
        open_excs = db.query(OperationsException).filter(OperationsException.status == "OPEN").all()
        exc_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total_financial_impact = 0.0
        for e in open_excs:
            exc_counts[e.severity] = exc_counts.get(e.severity, 0) + 1
            total_financial_impact += (e.financial_impact or 0.0)

        # 5. SLA Monitor
        sla_monitor = EntityViewService.get_sla_risk_monitor()
        sla_summary = sla_monitor.get("summary", {})

        # 6. Anomalies Scan
        wh_tables = WarehouseService.get_tables()
        anomalies_found = []
        for t in wh_tables[:3]:
            try:
                res = AnomalyService.detect_table_anomalies(t)
                for anom in res.get("anomalies", []):
                    anomalies_found.append({
                        "table": t,
                        "column": anom.get("column"),
                        "outlier_value": anom.get("outlier_value"),
                        "method": anom.get("method"),
                        "deviation_score": anom.get("deviation_score")
                    })
            except Exception:
                pass

        # 7. Formulate Top Priority Actions (ensure proposed actions exist)
        top_excs = sorted(open_excs, key=lambda x: x.priority_score or 0, reverse=True)[:5]
        actions_list = []
        for exc in top_excs:
            action = db.query(ActionItem).filter(ActionItem.exception_id == exc.id).first()
            if not action:
                action = ActionItem(
                    workspace_id=workspace_id,
                    exception_id=exc.id,
                    title=f"Resolve {exc.title}",
                    description=exc.description,
                    reason=f"Priority score {exc.priority_score:.1f} - financial impact: ${exc.financial_impact:,.2f}",
                    priority=exc.severity,
                    owner=exc.owner or "Operations Manager",
                    action_type="draft_email" if "overdue" in exc.exception_type else "create_task",
                    suggested_steps=[
                        "Inspect underlying database records",
                        "Contact responsible team or external partner",
                        "Apply corrective procedure per standard policy"
                    ],
                    affected_records=[exc.evidence] if exc.evidence else [],
                    status="PROPOSED",
                    approval_required=True
                )
                db.add(action)
                db.commit()
                db.refresh(action)
            actions_list.append({
                "action_id": action.id,
                "title": action.title,
                "priority": action.priority,
                "owner": action.owner,
                "status": action.status,
                "action_type": action.action_type,
                "reason": action.reason
            })

        # 8. Generate Executive AI Operations Brief
        prompt = f"""
You are the Chief AI Operations Copilot delivering the daily Morning Operations Review.
Here is today's audited state:
- Overall Data Health Score: {avg_health}%
- KPIs: {len(kpis)} active metrics ({kpi_counts.get('CRITICAL', 0)} Critical, {kpi_counts.get('WARNING', 0)} Warning, {kpi_counts.get('GOOD', 0)} On Target)
- Active Exceptions: {len(open_excs)} unresolved exceptions (${total_financial_impact:,.2f} total exposure)
- Critical Exceptions: {exc_counts.get('CRITICAL', 0)}, High: {exc_counts.get('HIGH', 0)}
- SLA Monitor: {sla_summary.get('breached_count', 0)} breached, {sla_summary.get('at_risk_count', 0)} at risk, ${sla_summary.get('financial_exposure', 0):,.2f} SLA exposure
- Statistical Anomalies: {len(anomalies_found)} detected

Generate a crisp, professional Executive Operations Brief structured with:
1. 🚦 Daily Operational Status (GREEN, AMBER, or RED with 1-line headline)
2. ⚠️ Critical Risks & Bottlenecks (Orders, Invoices, Tickets, Inventory)
3. 🎯 Priority Action Focus for Today (Top immediate decisions awaiting leadership approval)
4. 💡 Proactive Recommendation.
Use concise bullet points and bold numbers.
"""
        executive_brief = AIProvider.generate_text(prompt)

        duration_ms = int((time.time() - start_time) * 1000)

        # 9. Record WorkflowRun
        run = WorkflowRun(
            workflow_id=workflow.id,
            status="COMPLETED",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            records_processed=len(kpis) + len(open_excs) + len(anomalies_found),
            actions_created=len(actions_list),
            execution_log=[
                {"step": "Data Health", "status": "SUCCESS", "health_score": avg_health},
                {"step": "KPI Snapshot", "status": "SUCCESS", "kpi_counts": kpi_counts},
                {"step": "Rules & Exceptions", "status": "SUCCESS", "open_exceptions": len(open_excs)},
                {"step": "SLA Monitor", "status": "SUCCESS", "breaches": sla_summary.get('breached_count', 0)},
                {"step": "AI Operations Brief", "status": "SUCCESS", "duration_ms": duration_ms}
            ]
        )
        db.add(run)

        # Audit Event
        audit = AuditEvent(
            workspace_id=workspace_id,
            event_type="morning_review_run",
            entity_type="morning_review",
            entity_id=review_id,
            details={"duration_ms": duration_ms, "health_score": avg_health}
        )
        db.add(audit)
        db.commit()

        return {
            "review_id": review_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "data_health_score": avg_health,
            "kpi_summary": {
                "total_kpis": len(kpis),
                "counts": kpi_counts,
                "kpis": kpis
            },
            "exceptions_summary": {
                "total_open": len(open_excs),
                "severity_counts": exc_counts,
                "total_financial_impact": round(total_financial_impact, 2),
                "top_exceptions": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "severity": e.severity,
                        "priority_score": e.priority_score,
                        "financial_impact": e.financial_impact
                    } for e in top_excs
                ]
            },
            "anomalies_summary": {
                "total_detected": len(anomalies_found),
                "items": anomalies_found[:10]
            },
            "sla_summary": sla_summary,
            "todays_prioritized_actions": actions_list,
            "executive_brief": executive_brief,
            "duration_ms": duration_ms
        }
