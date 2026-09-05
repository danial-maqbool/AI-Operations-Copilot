from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    DataSourceTable, DataCatalogColumn, Relationship, DataSource, Workspace
)
from backend.schemas.catalog import (
    TableProfile, ColumnProfile, RelationshipResponse, ColumnOverrideRequest
)
from backend.services.profiler_service import ProfilerService

router = APIRouter(prefix="/catalog", tags=["Semantic Data Catalog"])

@router.get("/profile", response_model=List[TableProfile])
def profile_all(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    ProfilerService.profile_all_tables(workspace_id, db)
    
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
    if not ws:
        return []

    tables = db.query(DataSourceTable).join(DataSource).filter(DataSource.workspace_id == ws.id).all()
    results = []
    for tbl in tables:
        cols = db.query(DataCatalogColumn).filter(DataCatalogColumn.table_id == tbl.id).all()
        col_list = []
        for c in cols:
            col_list.append(ColumnProfile(
                id=c.id,
                table_id=c.table_id,
                table_name=tbl.table_name,
                column_name=c.column_name,
                data_type=c.data_type,
                inferred_role=c.inferred_role,
                user_role_override=c.user_role_override,
                inferred_description=c.inferred_description,
                user_description_override=c.user_description_override,
                null_count=c.null_count,
                null_percentage=c.null_percentage,
                unique_count=c.unique_count,
                sample_values=c.sample_values or [],
                is_primary_key=c.is_primary_key,
                is_foreign_key=c.is_foreign_key,
                is_sensitive=c.is_sensitive
            ))
            
        meta = tbl.schema_metadata or {}
        results.append(TableProfile(
            id=tbl.id,
            data_source_id=tbl.data_source_id,
            table_name=tbl.table_name,
            row_count=tbl.row_count,
            column_count=tbl.column_count,
            missing_cells_total=meta.get("missing_cells_total", 0),
            duplicate_rows=meta.get("duplicate_rows", 0),
            detected_entity=meta.get("detected_entity", "Operations Data"),
            columns=col_list,
            data_health_score=tbl.data_health_score
        ))
    return results

@router.get("/tables/{table_id}", response_model=TableProfile)
def get_table_profile(table_id: str, db: Session = Depends(get_db)):
    tbl = db.query(DataSourceTable).filter(DataSourceTable.id == table_id).first()
    if not tbl:
        raise HTTPException(status_code=404, detail="Table not found")
        
    cols = db.query(DataCatalogColumn).filter(DataCatalogColumn.table_id == tbl.id).all()
    col_list = [
        ColumnProfile(
            id=c.id,
            table_id=c.table_id,
            table_name=tbl.table_name,
            column_name=c.column_name,
            data_type=c.data_type,
            inferred_role=c.inferred_role,
            user_role_override=c.user_role_override,
            inferred_description=c.inferred_description,
            user_description_override=c.user_description_override,
            null_count=c.null_count,
            null_percentage=c.null_percentage,
            unique_count=c.unique_count,
            sample_values=c.sample_values or [],
            is_primary_key=c.is_primary_key,
            is_foreign_key=c.is_foreign_key,
            is_sensitive=c.is_sensitive
        )
        for c in cols
    ]
    meta = tbl.schema_metadata or {}
    return TableProfile(
        id=tbl.id,
        data_source_id=tbl.data_source_id,
        table_name=tbl.table_name,
        row_count=tbl.row_count,
        column_count=tbl.column_count,
        missing_cells_total=meta.get("missing_cells_total", 0),
        duplicate_rows=meta.get("duplicate_rows", 0),
        detected_entity=meta.get("detected_entity", "Operations Data"),
        columns=col_list,
        data_health_score=tbl.data_health_score
    )

@router.put("/columns/{column_id}")
def update_column_override(column_id: str, req: ColumnOverrideRequest, db: Session = Depends(get_db)):
    col = db.query(DataCatalogColumn).filter(DataCatalogColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
        
    if req.user_role_override is not None:
        col.user_role_override = req.user_role_override
    if req.user_description_override is not None:
        col.user_description_override = req.user_description_override
    if req.is_sensitive is not None:
        col.is_sensitive = req.is_sensitive
        
    db.commit()
    db.refresh(col)
    return {
        "id": col.id,
        "column_name": col.column_name,
        "user_role_override": col.user_role_override,
        "user_description_override": col.user_description_override,
        "is_sensitive": col.is_sensitive
    }

@router.get("/relationships", response_model=List[RelationshipResponse])
def get_relationships(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
    if not ws:
        return []
    return db.query(Relationship).filter(Relationship.workspace_id == ws.id).all()
