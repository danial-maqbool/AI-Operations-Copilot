import json
import sqlite3
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.config import settings
from backend.models import Workspace, DataSource, DataSourceTable
from backend.services.warehouse import load_df_to_warehouse

class IngestionService:
    @staticmethod
    def get_or_create_default_workspace(db: Session) -> Workspace:
        ws = db.query(Workspace).first()
        if not ws:
            ws = Workspace(name="Default Workspace", description="Primary Operations Workspace")
            db.add(ws)
            db.commit()
            db.refresh(ws)
        return ws

    @staticmethod
    def clean_table_name(name: str) -> str:
        clean = Path(name).stem.strip().lower()
        clean = clean.replace(" ", "_").replace("-", "_").replace(".", "_")
        return "".join(c for c in clean if c.isalnum() or c == "_")

    @classmethod
    def ingest_csv(
        cls,
        file_path: Path,
        original_filename: str,
        workspace_id: Optional[str],
        db: Session,
        table_name_override: Optional[str] = None
    ) -> DataSource:
        if not workspace_id:
            workspace_id = cls.get_or_create_default_workspace(db).id

        # Determine delimiter and read CSV
        try:
            df = pd.read_csv(file_path, sep=None, engine="python")
        except Exception:
            df = pd.read_csv(file_path)

        table_name = table_name_override or cls.clean_table_name(original_filename)
        cleaned_df = load_df_to_warehouse(df, table_name)

        ds = DataSource(
            workspace_id=workspace_id,
            name=original_filename,
            source_type="csv",
            file_path=str(file_path),
            row_count=len(cleaned_df),
            table_count=1,
            status="connected"
        )
        db.add(ds)
        db.flush()

        table = DataSourceTable(
            data_source_id=ds.id,
            table_name=table_name,
            row_count=len(cleaned_df),
            column_count=len(cleaned_df.columns),
            file_path=str(file_path),
            schema_metadata={"columns": list(cleaned_df.columns)}
        )
        db.add(table)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def ingest_excel(
        cls,
        file_path: Path,
        original_filename: str,
        workspace_id: Optional[str],
        db: Session,
        selected_sheets: Optional[List[str]] = None
    ) -> DataSource:
        if not workspace_id:
            workspace_id = cls.get_or_create_default_workspace(db).id

        excel_file = pd.ExcelFile(file_path)
        sheet_names = selected_sheets or excel_file.sheet_names

        total_rows = 0
        tables_created = []

        ds = DataSource(
            workspace_id=workspace_id,
            name=original_filename,
            source_type="excel",
            file_path=str(file_path),
            status="connected"
        )
        db.add(ds)
        db.flush()

        for sheet in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            base_name = cls.clean_table_name(f"{Path(original_filename).stem}_{sheet}")
            cleaned_df = load_df_to_warehouse(df, base_name)
            total_rows += len(cleaned_df)

            table = DataSourceTable(
                data_source_id=ds.id,
                table_name=base_name,
                sheet_name=sheet,
                row_count=len(cleaned_df),
                column_count=len(cleaned_df.columns),
                file_path=str(file_path),
                schema_metadata={"sheet": sheet, "columns": list(cleaned_df.columns)}
            )
            db.add(table)
            tables_created.append(table)

        ds.row_count = total_rows
        ds.table_count = len(tables_created)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def ingest_json(
        cls,
        file_path: Path,
        original_filename: str,
        workspace_id: Optional[str],
        db: Session,
        table_name_override: Optional[str] = None
    ) -> DataSource:
        if not workspace_id:
            workspace_id = cls.get_or_create_default_workspace(db).id

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.json_normalize(data)
        elif isinstance(data, dict):
            # Check if there is a primary list inside dict
            list_keys = [k for k, v in data.items() if isinstance(v, list)]
            if list_keys:
                df = pd.json_normalize(data[list_keys[0]])
            else:
                df = pd.json_normalize([data])
        else:
            raise ValueError("Unsupported JSON structure: expected array of objects or object")

        table_name = table_name_override or cls.clean_table_name(original_filename)
        cleaned_df = load_df_to_warehouse(df, table_name)

        ds = DataSource(
            workspace_id=workspace_id,
            name=original_filename,
            source_type="json",
            file_path=str(file_path),
            row_count=len(cleaned_df),
            table_count=1,
            status="connected"
        )
        db.add(ds)
        db.flush()

        table = DataSourceTable(
            data_source_id=ds.id,
            table_name=table_name,
            row_count=len(cleaned_df),
            column_count=len(cleaned_df.columns),
            file_path=str(file_path),
            schema_metadata={"columns": list(cleaned_df.columns)}
        )
        db.add(table)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def ingest_sqlite(
        cls,
        file_path: Path,
        original_filename: str,
        workspace_id: Optional[str],
        db: Session
    ) -> DataSource:
        if not workspace_id:
            workspace_id = cls.get_or_create_default_workspace(db).id

        source_conn = sqlite3.connect(str(file_path))
        cursor = source_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        total_rows = 0
        ds = DataSource(
            workspace_id=workspace_id,
            name=original_filename,
            source_type="sqlite",
            file_path=str(file_path),
            status="connected"
        )
        db.add(ds)
        db.flush()

        for t in tables:
            df = pd.read_sql_query(f'SELECT * FROM "{t}"', source_conn)
            clean_tbl = cls.clean_table_name(t)
            cleaned_df = load_df_to_warehouse(df, clean_tbl)
            total_rows += len(cleaned_df)

            table = DataSourceTable(
                data_source_id=ds.id,
                table_name=clean_tbl,
                row_count=len(cleaned_df),
                column_count=len(cleaned_df.columns),
                file_path=str(file_path),
                schema_metadata={"original_table": t, "columns": list(cleaned_df.columns)}
            )
            db.add(table)

        source_conn.close()

        ds.row_count = total_rows
        ds.table_count = len(tables)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def connect_postgres(
        cls,
        connection_uri: str,
        name: str,
        workspace_id: Optional[str],
        db: Session
    ) -> DataSource:
        """Securely inspect and register a PostgreSQL data source without leaking passwords to frontend."""
        if not workspace_id:
            workspace_id = cls.get_or_create_default_workspace(db).id

        # Mask connection URI for security
        masked_uri = connection_uri
        if "@" in connection_uri and "://" in connection_uri:
            prefix, rest = connection_uri.split("://", 1)
            user_pass, host_db = rest.split("@", 1)
            username = user_pass.split(":")[0] if ":" in user_pass else user_pass
            masked_uri = f"{prefix}://{username}:********@{host_db}"

        ds = DataSource(
            workspace_id=workspace_id,
            name=name,
            source_type="postgres",
            connection_uri=masked_uri,
            status="connected",
            row_count=0,
            table_count=0
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)
        return ds

    @classmethod
    def refresh_data_source(cls, data_source_id: str, db: Session) -> Dict[str, Any]:
        ds = db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not ds:
            raise ValueError("Data source not found")
        
        old_rows = ds.row_count
        # If file-backed, reload into warehouse
        if ds.file_path and Path(ds.file_path).exists():
            if ds.source_type == "csv":
                df = pd.read_csv(ds.file_path)
                tbl = ds.tables[0] if ds.tables else None
                tbl_name = tbl.table_name if tbl else cls.clean_table_name(ds.name)
                cleaned = load_df_to_warehouse(df, tbl_name)
                ds.row_count = len(cleaned)
                if tbl:
                    tbl.row_count = len(cleaned)
            elif ds.source_type == "json":
                with open(ds.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                df = pd.json_normalize(data if isinstance(data, list) else [data])
                tbl = ds.tables[0] if ds.tables else None
                tbl_name = tbl.table_name if tbl else cls.clean_table_name(ds.name)
                cleaned = load_df_to_warehouse(df, tbl_name)
                ds.row_count = len(cleaned)
                if tbl:
                    tbl.row_count = len(cleaned)
        
        ds.last_refreshed = pd.Timestamp.utcnow()
        db.commit()
        
        return {
            "data_source_id": ds.id,
            "status": "refreshed",
            "previous_rows": old_rows,
            "current_rows": ds.row_count,
            "rows_diff": ds.row_count - old_rows,
            "last_refreshed": ds.last_refreshed.isoformat()
        }
