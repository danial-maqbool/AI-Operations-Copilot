from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.workflow import MorningReviewResponse
from backend.services.morning_review import MorningReviewService

router = APIRouter(prefix="/morning-review", tags=["Morning Operations Review"])

@router.post("/run", response_model=MorningReviewResponse)
def run_morning_review(db: Session = Depends(get_db)):
    """
    Executes the signature one-click Morning Operations Review:
    - Verifies data health
    - Updates KPI snapshots
    - Evaluates business rules & exceptions
    - Scans SLA breaches
    - Detects operational anomalies
    - Generates today's prioritized action plan
    - Synthesizes executive AI operations brief
    """
    try:
        return MorningReviewService.run_morning_review(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute morning review: {str(e)}")

@router.get("/latest", response_model=MorningReviewResponse)
def get_latest_morning_review(db: Session = Depends(get_db)):
    """
    Returns the latest morning review or runs a fresh one.
    """
    try:
        return MorningReviewService.run_morning_review(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch morning review: {str(e)}")
