import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.all_models import Report
from backend.schemas.report import ReportGenerateRequest, ReportResponse
from backend.services.report_service import ReportService, EXPORTS_DIR

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])

def format_report_response(report: Report) -> Dict[str, Any]:
    base_file = os.path.basename(report.file_path) if report.file_path else f"report_{report.id}"
    name_no_ext = os.path.splitext(base_file)[0]
    return {
        "id": report.id,
        "workspace_id": report.workspace_id,
        "title": report.title,
        "period": report.period,
        "report_type": report.report_type,
        "sections": report.sections or {},
        "export_formats": report.export_formats or ["xlsx", "json", "csv"],
        "file_path": report.file_path,
        "download_urls": {
            "xlsx": f"/api/reports/download/{name_no_ext}.xlsx",
            "json": f"/api/reports/download/{name_no_ext}.json",
            "csv": f"/api/reports/download/{name_no_ext}.csv"
        },
        "created_at": report.created_at
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_reports(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """
    Returns list of previously generated executive reports.
    """
    reports = ReportService.list_reports(db, limit=limit)
    return [format_report_response(r) for r in reports]

@router.post("/generate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a full operational report in Excel (.xlsx), CSV, and JSON formats.
    """
    try:
        report = ReportService.generate_report(db, payload)
        return format_report_response(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/{report_id}", response_model=Dict[str, Any])
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return format_report_response(report)

@router.get("/download/{filename}")
def download_export(filename: str):
    """
    Safely downloads generated report files (XLSX, CSV, JSON) from exports directory.
    """
    # Prevent path traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(EXPORTS_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{safe_filename}' not found.")
    
    media_type = "application/octet-stream"
    if safe_filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif safe_filename.endswith(".json"):
        media_type = "application/json"
    elif safe_filename.endswith(".csv"):
        media_type = "text/csv"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=safe_filename
    )
