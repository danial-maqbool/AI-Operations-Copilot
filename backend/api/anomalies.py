from typing import List, Optional
from fastapi import APIRouter, HTTPException
from backend.schemas.anomaly import AnomalyScanRequest, AnomalyScanResponse
from backend.services.anomaly_service import AnomalyDetectionService
from backend.services.warehouse import get_warehouse_tables

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection Engine"])

@router.post("/scan", response_model=AnomalyScanResponse)
def scan_table(req: AnomalyScanRequest):
    try:
        return AnomalyDetectionService.scan_table(
            table_name=req.table_name,
            columns=req.columns,
            method=req.method,
            threshold=req.threshold
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/summary")
def get_anomaly_summary():
    tables = get_warehouse_tables()
    summary = []
    total_anomalies = 0

    for t in tables:
        try:
            res = AnomalyDetectionService.scan_table(t, method="z_score", threshold=3.0)
            total_anomalies += res.anomalies_detected
            summary.append({
                "table_name": t,
                "anomalies_count": res.anomalies_detected,
                "records_analyzed": res.total_records_analyzed,
                "top_items": res.items[:3]
            })
        except Exception:
            continue

    return {
        "total_anomalies_flagged": total_anomalies,
        "tables_analyzed": len(tables),
        "tables": summary
    }
