from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BusinessRule, Workspace
from backend.schemas.rule import BusinessRuleCreate, BusinessRuleResponse, ExceptionResponse
from backend.services.rule_engine import BusinessRuleEngine

router = APIRouter(prefix="/rules", tags=["Business Rule Engine"])

@router.get("", response_model=List[BusinessRuleResponse])
def list_rules(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
    if not ws:
        return []
    BusinessRuleEngine.seed_default_rules(ws.id, db)
    return db.query(BusinessRule).filter(BusinessRule.workspace_id == ws.id).all()

@router.post("", response_model=BusinessRuleResponse)
def create_rule(req: BusinessRuleCreate, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == req.workspace_id).first() if req.workspace_id else db.query(Workspace).first()
    if not ws:
        raise HTTPException(status_code=400, detail="No workspace available")

    rule = BusinessRule(
        workspace_id=ws.id,
        name=req.name,
        entity=req.entity,
        target_table=req.target_table,
        conditions=[c.dict() for c in req.conditions],
        severity=req.severity,
        action_template=req.action_template or {},
        is_active=req.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted", "id": rule_id}

@router.post("/evaluate", response_model=List[ExceptionResponse])
def evaluate_rules(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    exceptions = BusinessRuleEngine.evaluate_all_rules(workspace_id, db)
    return exceptions
