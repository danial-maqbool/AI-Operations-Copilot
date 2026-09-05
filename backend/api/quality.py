from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.quality import WorkspaceQualitySummary, TableQualityReport
from backend.services.quality_service import DataQualityEngine

router = APIRouter(prefix="/quality", tags=["Data Quality Engine"])

@router.get("/audit", response_model=WorkspaceQualitySummary)
def run_quality_audit(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        return DataQualityEngine.run_workspace_audit(workspace_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality audit failed: {str(e)}")
