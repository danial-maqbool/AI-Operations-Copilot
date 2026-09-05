from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Metric, Workspace
from backend.schemas.kpi import (
    MetricCreate, MetricUpdate, MetricResponse, TestMetricRequest
)
from backend.services.kpi_service import KPIService

router = APIRouter(prefix="/metrics", tags=["KPI Engine"])

@router.get("", response_model=List[MetricResponse])
def get_metrics(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    return KPIService.get_all_metrics(workspace_id, db)

@router.post("", response_model=MetricResponse)
def create_metric(req: MetricCreate, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == req.workspace_id).first() if req.workspace_id else db.query(Workspace).first()
    if not ws:
        raise HTTPException(status_code=400, detail="No workspace available")

    # Verify code uniqueness
    existing = db.query(Metric).filter(Metric.workspace_id == ws.id, Metric.code == req.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Metric with code '{req.code}' already exists")

    new_m = Metric(
        workspace_id=ws.id,
        name=req.name,
        code=req.code,
        description=req.description,
        source_table=req.source_table,
        formula=req.formula,
        time_column=req.time_column,
        aggregation=req.aggregation,
        target_value=req.target_value,
        warning_threshold=req.warning_threshold,
        critical_threshold=req.critical_threshold,
        comparison_direction=req.comparison_direction,
        owner=req.owner
    )
    db.add(new_m)
    db.commit()
    db.refresh(new_m)
    return KPIService.evaluate_metric(new_m, period="Current", db=db)

@router.get("/{metric_id}", response_model=MetricResponse)
def get_metric(metric_id: str, period: str = "this_month", db: Session = Depends(get_db)):
    metric = db.query(Metric).filter(Metric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return KPIService.evaluate_metric(metric, period=period, db=db)

@router.put("/{metric_id}", response_model=MetricResponse)
def update_metric(metric_id: str, req: MetricUpdate, db: Session = Depends(get_db)):
    metric = db.query(Metric).filter(Metric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    for k, v in req.dict(exclude_unset=True).items():
        setattr(metric, k, v)

    db.commit()
    db.refresh(metric)
    return KPIService.evaluate_metric(metric, period="Current", db=db)

@router.delete("/{metric_id}")
def delete_metric(metric_id: str, db: Session = Depends(get_db)):
    metric = db.query(Metric).filter(Metric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    db.delete(metric)
    db.commit()
    return {"status": "deleted", "id": metric_id}

@router.post("/test")
def test_metric(req: TestMetricRequest):
    try:
        return KPIService.test_formula(req.source_table, req.formula)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
