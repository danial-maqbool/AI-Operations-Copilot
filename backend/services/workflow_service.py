import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.models.all_models import (
    Workflow, WorkflowRun, Workspace, DataSourceTable, AuditEvent, ActionItem, OperationsException
)
from backend.schemas.workflow import WorkflowCreate, WorkflowUpdate
from backend.services.kpi_service import KPIService
from backend.services.rule_engine import RuleEngine
from backend.services.anomaly_service import AnomalyService
from backend.services.entity_views import EntityViewService
from backend.services.warehouse import WarehouseService
from backend.services.ai_provider import AIProvider

class WorkflowService:
    @staticmethod
    def get_or_create_default_workspace(db: Session) -> str:
        ws = db.query(Workspace).first()
        if not ws:
            ws = Workspace(name="Default Workspace")
            db.add(ws)
            db.commit()
            db.refresh(ws)
        return ws.id

    @staticmethod
    def list_workflows(db: Session) -> List[Workflow]:
        return db.query(Workflow).order_by(Workflow.created_at.desc()).all()

    @staticmethod
    def get_workflow(db: Session, workflow_id: str) -> Optional[Workflow]:
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()

    @staticmethod
    def create_workflow(db: Session, payload: WorkflowCreate) -> Workflow:
        workspace_id = payload.workspace_id or WorkflowService.get_or_create_default_workspace(db)
        wf = Workflow(
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            trigger_type=payload.trigger_type,
            steps=payload.steps,
            is_active=payload.is_active
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        return wf

    @staticmethod
    def update_workflow(db: Session, workflow_id: str, payload: WorkflowUpdate) -> Optional[Workflow]:
        wf = WorkflowService.get_workflow(db, workflow_id)
        if not wf:
            return None
        
        data = payload.model_dump(exclude_unset=True)
        for key, val in data.items():
            setattr(wf, key, val)
        
        wf.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(wf)
        return wf

    @staticmethod
    def delete_workflow(db: Session, workflow_id: str) -> bool:
        wf = WorkflowService.get_workflow(db, workflow_id)
        if not wf:
            return False
        db.delete(wf)
        db.commit()
        return True

    @staticmethod
    def run_workflow(db: Session, workflow_id: str) -> WorkflowRun:
        wf = WorkflowService.get_workflow(db, workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        run = WorkflowRun(
            workflow_id=wf.id,
            status="RUNNING",
            started_at=datetime.utcnow(),
            execution_log=[],
            records_processed=0,
            actions_created=0
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        log = []
        total_records = 0
        actions_created = 0

        try:
            for step in wf.steps or []:
                step_name = step.get("name", "Step")
                step_type = step.get("step_type", "")
                step_start = time.time()

                step_log = {"step": step_name, "type": step_type, "status": "STARTED"}

                if step_type == "calculate_kpis":
                    kpis = KPIService.get_all_kpi_snapshots(db)
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"Calculated {len(kpis)} KPI snapshots"
                    total_records += len(kpis)

                elif step_type == "evaluate_rules":
                    exceptions = RuleEngine.evaluate_all_rules(db)
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"Evaluated rules, identified {len(exceptions)} exceptions"
                    total_records += len(exceptions)

                elif step_type == "check_sla_breaches":
                    sla_res = EntityViewService.get_sla_risk_monitor()
                    breached = sla_res.get("summary", {}).get("breached_count", 0)
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"SLA monitor scanned: {breached} breaches detected"
                    total_records += breached

                elif step_type == "detect_anomalies":
                    tables = WarehouseService.get_tables()
                    anom_count = 0
                    for t in tables[:3]:
                        try:
                            res = AnomalyService.detect_table_anomalies(t)
                            anom_count += res.get("total_anomalies", 0)
                        except Exception:
                            pass
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"Scanned tables, detected {anom_count} anomalies"

                elif step_type == "generate_action_plan":
                    # Look up open critical/high exceptions without action items
                    open_excs = db.query(OperationsException).filter(
                        OperationsException.status == "OPEN",
                        OperationsException.severity.in_(["CRITICAL", "HIGH"])
                    ).limit(5).all()

                    for exc in open_excs:
                        existing = db.query(ActionItem).filter(ActionItem.exception_id == exc.id).first()
                        if not existing:
                            action = ActionItem(
                                workspace_id=wf.workspace_id,
                                exception_id=exc.id,
                                title=f"Resolve {exc.title}",
                                description=exc.description,
                                reason=f"Exception {exc.exception_type} requires operational action",
                                priority=exc.severity,
                                owner=exc.owner or "Operations Lead",
                                action_type="create_task" if "order" not in exc.exception_type else "draft_email",
                                suggested_steps=["Verify affected entity", "Execute resolution policy", "Verify SLA closure"],
                                status="PROPOSED",
                                approval_required=True
                            )
                            db.add(action)
                            actions_created += 1

                    db.commit()
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"Generated {actions_created} proposed action items"

                else:
                    step_log["status"] = "SUCCESS"
                    step_log["detail"] = f"Custom step {step_name} executed"

                step_log["duration_ms"] = int((time.time() - step_start) * 1000)
                log.append(step_log)

            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.execution_log = log
            run.records_processed = total_records
            run.actions_created = actions_created
            db.commit()

            # Audit Event
            audit = AuditEvent(
                workspace_id=wf.workspace_id,
                event_type="workflow_run",
                entity_type="workflow",
                entity_id=wf.id,
                details={
                    "workflow_name": wf.name,
                    "records_processed": total_records,
                    "actions_created": actions_created
                }
            )
            db.add(audit)
            db.commit()

        except Exception as e:
            run.status = "FAILED"
            run.completed_at = datetime.utcnow()
            run.error_message = str(e)
            run.execution_log = log
            db.commit()

        db.refresh(run)
        return run
