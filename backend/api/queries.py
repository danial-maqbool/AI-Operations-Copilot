from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.sql_safety import SQLSafetyValidator, SQLSafetyError
from backend.models import AuditEvent, Workspace

router = APIRouter(prefix="/queries", tags=["Safe SQL Engine"])

@router.post("/execute", response_model=QueryResponse)
def execute_query(req: QueryRequest, db: Session = Depends(get_db)):
    try:
        result = SQLSafetyValidator.execute_safe_query(req.sql)
        
        # Log to Audit Log
        ws = db.query(Workspace).filter(Workspace.id == req.workspace_id).first() if req.workspace_id else db.query(Workspace).first()
        if ws:
            audit = AuditEvent(
                workspace_id=ws.id,
                event_type="sql_executed",
                user_name="Analyst",
                details={
                    "sql": req.sql,
                    "sanitized_sql": result["sanitized_sql"],
                    "rows_returned": result["total_rows"],
                    "duration_ms": result["duration_ms"],
                    "success": result["success"]
                },
                status="SUCCESS" if result["success"] else "FAILED"
            )
            db.add(audit)
            db.commit()

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return QueryResponse(**result)
    except SQLSafetyError as e:
        raise HTTPException(status_code=400, detail=f"SQL Safety Violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")

@router.post("/validate")
def validate_query(req: QueryRequest):
    try:
        sanitized_sql, tables, explanation = SQLSafetyValidator.validate_and_sanitize(req.sql)
        return {
            "valid": True,
            "sanitized_sql": sanitized_sql,
            "referenced_tables": tables,
            "explanation": explanation
        }
    except SQLSafetyError as e:
        return {
            "valid": False,
            "error": str(e)
        }
