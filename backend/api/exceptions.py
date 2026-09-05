from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import OperationsException, Workspace
from backend.schemas.rule import ExceptionResponse, ExceptionStatusUpdate

router = APIRouter(prefix="/exceptions", tags=["Operations Exceptions"])

@router.get("", response_model=List[ExceptionResponse])
def list_exceptions(
    workspace_id: Optional[str] = None,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(OperationsException)
    if workspace_id:
        query = query.filter(OperationsException.workspace_id == workspace_id)
    if status:
        query = query.filter(OperationsException.status == status)
    if severity:
        query = query.filter(OperationsException.severity == severity)
    if entity_type:
        query = query.filter(OperationsException.entity_type == entity_type)

    # Order by priority_score descending
    return query.order_by(OperationsException.priority_score.desc()).all()

@router.get("/{exception_id}", response_model=ExceptionResponse)
def get_exception(exception_id: str, db: Session = Depends(get_db)):
    exc = db.query(OperationsException).filter(OperationsException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exc

@router.patch("/{exception_id}", response_model=ExceptionResponse)
def update_exception_status(exception_id: str, req: ExceptionStatusUpdate, db: Session = Depends(get_db)):
    exc = db.query(OperationsException).filter(OperationsException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    exc.status = req.status
    db.commit()
    db.refresh(exc)
    return exc
