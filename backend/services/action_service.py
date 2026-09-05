import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.all_models import ActionItem, OperationsException, AuditEvent, Workspace
from backend.schemas.action import ActionItemCreate, ActionApprovalRequest

EXPORTS_DIR = os.path.join(os.getcwd(), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

class ActionService:
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
    def list_actions(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        owner: Optional[str] = None,
        limit: int = 100
    ) -> List[ActionItem]:
        query = db.query(ActionItem)
        if status:
            query = query.filter(ActionItem.status == status.upper())
        if priority:
            query = query.filter(ActionItem.priority == priority.upper())
        if owner:
            query = query.filter(ActionItem.owner.ilike(f"%{owner}%"))
        
        return query.order_by(ActionItem.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_action_by_id(db: Session, action_id: str) -> Optional[ActionItem]:
        return db.query(ActionItem).filter(ActionItem.id == action_id).first()

    @staticmethod
    def create_action(db: Session, payload: ActionItemCreate) -> ActionItem:
        workspace_id = payload.workspace_id or ActionService.get_or_create_default_workspace(db)
        
        action = ActionItem(
            workspace_id=workspace_id,
            exception_id=payload.exception_id,
            title=payload.title,
            description=payload.description,
            reason=payload.reason,
            source_finding=payload.source_finding,
            priority=payload.priority.upper(),
            owner=payload.owner,
            due_date=payload.due_date,
            suggested_steps=payload.suggested_steps,
            affected_records=payload.affected_records,
            action_type=payload.action_type,
            status="PROPOSED",
            approval_required=payload.approval_required,
            rejection_reason=None,
            approved_by=None,
            execution_result={}
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        audit = AuditEvent(
            workspace_id=workspace_id,
            event_type="action_proposed",
            entity_type="action",
            entity_id=action.id,
            details={
                "title": action.title,
                "priority": action.priority,
                "action_type": action.action_type,
                "owner": action.owner
            }
        )
        db.add(audit)
        db.commit()

        return action

    @staticmethod
    def approve_or_reject(db: Session, action_id: str, request: ActionApprovalRequest) -> ActionItem:
        action = ActionService.get_action_by_id(db, action_id)
        if not action:
            raise ValueError(f"Action with ID '{action_id}' not found.")

        decision = request.action.lower()
        if decision == "approve":
            action.status = "APPROVED"
            action.approved_by = request.approved_by or "Operations Manager"
            action.rejection_reason = None
            
            audit = AuditEvent(
                workspace_id=action.workspace_id,
                event_type="action_approved",
                user_name=action.approved_by,
                entity_type="action",
                entity_id=action.id,
                details={"approved_by": action.approved_by}
            )
            db.add(audit)
        elif decision == "reject":
            action.status = "REJECTED"
            action.rejection_reason = request.rejection_reason or "No reason specified."
            action.approved_by = request.approved_by or "Operations Manager"
            
            audit = AuditEvent(
                workspace_id=action.workspace_id,
                event_type="action_rejected",
                user_name=action.approved_by,
                entity_type="action",
                entity_id=action.id,
                details={"rejection_reason": action.rejection_reason}
            )
            db.add(audit)
        else:
            raise ValueError("Decision must be either 'approve' or 'reject'.")

        action.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def execute_action(db: Session, action_id: str, executed_by: str = "Operations Lead") -> Dict[str, Any]:
        action = ActionService.get_action_by_id(db, action_id)
        if not action:
            raise ValueError(f"Action with ID '{action_id}' not found.")

        if action.approval_required and action.status != "APPROVED":
            raise ValueError(f"Cannot execute action in status '{action.status}'. Action must be APPROVED first.")

        action_type = action.action_type or "create_task"
        result: Dict[str, Any] = {}

        if action_type == "export_csv":
            filename = f"action_export_{action.id[:8]}_{int(datetime.utcnow().timestamp())}.csv"
            filepath = os.path.join(EXPORTS_DIR, filename)
            
            records = action.affected_records or []
            if records and isinstance(records, list) and isinstance(records[0], dict):
                fieldnames = list(records[0].keys())
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
            else:
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    f.write("id,title,description,reason\n")
                    f.write(f'"{action.id}","{action.title}","{action.description or ""}","{action.reason or ""}"\n')
            
            result = {
                "execution_type": "export_csv",
                "file_path": filepath,
                "file_name": filename,
                "records_exported": len(records),
                "download_url": f"/api/reports/download?filename={filename}",
                "message": f"Successfully exported {len(records)} records to {filename}"
            }

        elif action_type == "draft_email":
            recipient = "customer-ops@example.com"
            if action.affected_records and isinstance(action.affected_records[0], dict):
                first = action.affected_records[0]
                recipient = first.get("email") or first.get("customer_email") or recipient

            subject = f"URGENT OPS UPDATE: {action.title}"
            body_lines = [
                "Dear Operations Team / Partner,",
                "",
                f"Regarding: {action.title}",
                f"Context: {action.reason or action.description or 'Operational resolution needed'}",
                "",
                "Suggested Steps:"
            ]
            for step in action.suggested_steps or ["Inspect record", "Apply corrective resolution"]:
                body_lines.append(f"  * {step}")
            body_lines.extend([
                "",
                f"Generated by OpsPilot on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "OpsPilot Operations Intelligence"
            ])
            body = "\n".join(body_lines)

            result = {
                "execution_type": "draft_email",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "status": "DRAFT_READY",
                "message": f"Email draft successfully created for {recipient}"
            }

        elif action_type == "call_list":
            contacts = []
            for rec in (action.affected_records or []):
                if isinstance(rec, dict):
                    contacts.append({
                        "name": rec.get("customer_name") or rec.get("name") or "Contact",
                        "phone": rec.get("phone") or rec.get("contact_number") or "N/A",
                        "account": rec.get("customer_id") or rec.get("account_id") or "N/A",
                        "balance": rec.get("amount") or rec.get("overdue_balance") or rec.get("total_amount") or 0.0,
                        "script": f"Hi, calling from Operations regarding {action.title}. Can we assist with payment or order fulfillment today?"
                    })
            if not contacts:
                contacts.append({
                    "name": "Primary Account Contact",
                    "phone": "N/A",
                    "account": "Direct Follow-up",
                    "balance": 0.0,
                    "script": f"Inquiring regarding operational exception: {action.title}"
                })
            
            result = {
                "execution_type": "call_list",
                "total_contacts": len(contacts),
                "contacts": contacts,
                "message": f"Call list generated with {len(contacts)} contacts"
            }

        else:
            result = {
                "execution_type": "create_task",
                "task_id": f"TASK-{action.id[:8].upper()}",
                "assigned_to": action.owner,
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "checklist": action.suggested_steps or ["Review affected entity", "Execute policy adjustment", "Verify status"],
                "message": f"Internal Operations task created for {action.owner}"
            }

        action.status = "COMPLETED"
        action.executed_at = datetime.utcnow()
        action.execution_result = result
        action.updated_at = datetime.utcnow()

        if action.exception_id:
            exc = db.query(OperationsException).filter(OperationsException.id == action.exception_id).first()
            if exc:
                exc.status = "RESOLVED"
                exc.updated_at = datetime.utcnow()

        audit = AuditEvent(
            workspace_id=action.workspace_id,
            event_type="action_executed",
            user_name=executed_by,
            entity_type="action",
            entity_id=action.id,
            details={
                "action_type": action_type,
                "execution_result": result
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(action)

        return result
