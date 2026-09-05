import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from backend.database import get_db
from backend.config import settings
from backend.models import DataSource, DataSourceTable
from backend.schemas.data_source import DataSourceResponse, PostgresConnectRequest
from backend.services.ingestion_service import IngestionService
from backend.services.warehouse import query_warehouse

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])

@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DataSource)
    if workspace_id:
        query = query.filter(DataSource.workspace_id == workspace_id)
    return query.all()

@router.post("/upload", response_model=DataSourceResponse)
async def upload_file(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ext = Path(file.filename).suffix.lower()
    allowed_exts = [".csv", ".xlsx", ".xls", ".json", ".sqlite", ".db"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Allowed: {allowed_exts}")

    save_dir = settings.UPLOADS_DIR
    target_path = save_dir / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if ext == ".csv":
        ds = IngestionService.ingest_csv(target_path, file.filename, workspace_id, db)
    elif ext in [".xlsx", ".xls"]:
        ds = IngestionService.ingest_excel(target_path, file.filename, workspace_id, db)
    elif ext == ".json":
        ds = IngestionService.ingest_json(target_path, file.filename, workspace_id, db)
    elif ext in [".sqlite", ".db"]:
        ds = IngestionService.ingest_sqlite(target_path, file.filename, workspace_id, db)
    else:
        raise HTTPException(status_code=400, detail="Unhandled file type")

    return ds

@router.post("/postgres", response_model=DataSourceResponse)
def connect_postgres(req: PostgresConnectRequest, db: Session = Depends(get_db)):
    ds = IngestionService.connect_postgres(req.connection_uri, req.name, req.workspace_id, db)
    return ds

@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(data_source_id: str, db: Session = Depends(get_db)):
    ds = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    return ds

@router.post("/{data_source_id}/refresh")
def refresh_data_source(data_source_id: str, db: Session = Depends(get_db)):
    try:
        return IngestionService.refresh_data_source(data_source_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{data_source_id}")
def delete_data_source(data_source_id: str, db: Session = Depends(get_db)):
    ds = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    db.delete(ds)
    db.commit()
    return {"status": "deleted", "id": data_source_id}

@router.get("/{data_source_id}/preview/{table_name}")
def preview_table(data_source_id: str, table_name: str, db: Session = Depends(get_db)):
    # Verify table belongs to data source
    tbl = (
        db.query(DataSourceTable)
        .filter(DataSourceTable.data_source_id == data_source_id, DataSourceTable.table_name == table_name)
        .first()
    )
    if not tbl:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found for this source")

    try:
        df = query_warehouse(f'SELECT * FROM "{table_name}" LIMIT 20')
        return {
            "table_name": table_name,
            "columns": list(df.columns),
            "rows": df.where(pd.notnull(df), None).to_dict(orient="records"),
            "total_rows": tbl.row_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing table: {str(e)}")
