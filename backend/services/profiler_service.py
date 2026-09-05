import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.models import (
    DataSourceTable, DataCatalogColumn, Relationship, DataSource, Workspace
)
from backend.services.warehouse import warehouse_engine, query_warehouse

SENSITIVE_KEYWORDS = ["email", "phone", "ssn", "salary", "credit_card", "password", "bank", "token", "secret"]
STATUS_KEYWORDS = ["status", "state", "stage", "phase", "condition"]
DATE_KEYWORDS = ["date", "time", "at", "created", "updated", "timestamp", "promised", "delivered", "due"]
METRIC_KEYWORDS = ["amount", "price", "cost", "total", "revenue", "qty", "quantity", "discount", "balance", "margin", "count", "fee"]

ENTITY_DEFINITIONS = {
    "Customers": ["customer_id", "customer_name", "client", "buyer"],
    "Orders": ["order_id", "order_date", "total_amount", "promised_date"],
    "Products": ["product_id", "product_name", "sku", "unit_price"],
    "Inventory": ["inventory_id", "quantity_on_hand", "stock", "reorder_level", "warehouse"],
    "Invoices": ["invoice_id", "invoice_date", "due_date", "unpaid_amount", "outstanding"],
    "Payments": ["payment_id", "payment_date", "payment_method", "transaction_id"],
    "Tickets": ["ticket_id", "support_ticket", "issue_type", "sla_deadline", "priority"],
    "Shipments": ["shipment_id", "tracking_number", "carrier", "delivery_date", "shipped_date"],
    "Employees": ["employee_id", "staff_id", "department", "manager_id", "hire_date"]
}

class ProfilerService:
    @classmethod
    def profile_column(cls, series: pd.Series, col_name: str, table_name: str) -> Dict[str, Any]:
        total_count = len(series)
        null_count = int(series.isnull().sum())
        null_pct = round((null_count / total_count) * 100, 2) if total_count > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        
        # Sample non-null values
        valid_series = series.dropna()
        sample_vals = valid_series.head(5).tolist() if len(valid_series) > 0 else []
        # Convert any timestamps or numpy types to standard python
        clean_samples = []
        for v in sample_vals:
            if isinstance(v, (pd.Timestamp, np.datetime64)):
                clean_samples.append(str(v))
            elif isinstance(v, (np.integer, np.int64)):
                clean_samples.append(int(v))
            elif isinstance(v, (np.floating, np.float64)):
                clean_samples.append(float(v))
            else:
                clean_samples.append(str(v))

        # Check sensitivity
        is_sensitive = any(kw in col_name.lower() for kw in SENSITIVE_KEYWORDS)
        
        # Check primary key heuristic
        is_pk = False
        if null_count == 0 and unique_count == total_count and total_count > 0:
            if col_name.lower() == "id" or col_name.lower() == f"{table_name.rstrip('s')}_id" or col_name.lower().endswith("_id"):
                is_pk = True

        # Check foreign key heuristic
        is_fk = False
        if not is_pk and col_name.lower().endswith("_id"):
            is_fk = True

        # Determine data type & role
        dtype_str = str(series.dtype).lower()
        stats = {}
        inferred_role = "category"

        if is_sensitive:
            inferred_role = "sensitive"
            inferred_desc = f"Sensitive customer or employee information: {col_name}"
        elif is_pk:
            inferred_role = "identifier"
            inferred_desc = f"Unique primary identifier for {table_name}"
        elif is_fk:
            inferred_role = "identifier"
            inferred_desc = f"Foreign reference identifier linking to related entity"
        elif any(kw in col_name.lower() for kw in STATUS_KEYWORDS) or (unique_count <= 15 and not pd.api.types.is_numeric_dtype(series.dtype)):
            inferred_role = "status" if any(kw in col_name.lower() for kw in STATUS_KEYWORDS) else "category"
            top_vals = valid_series.value_counts().head(5).to_dict()
            stats["top_categories"] = {str(k): int(v) for k, v in top_vals.items()}
            cats = ", ".join(list(stats["top_categories"].keys())[:4])
            inferred_desc = f"Categorical values including: {cats}"
        elif any(kw in col_name.lower() for kw in DATE_KEYWORDS) or pd.api.types.is_datetime64_any_dtype(series.dtype):
            inferred_role = "business_date"
            try:
                dt_s = pd.to_datetime(valid_series, errors="coerce").dropna()
                if len(dt_s) > 0:
                    stats["min_date"] = str(dt_s.min())
                    stats["max_date"] = str(dt_s.max())
            except Exception:
                pass
            inferred_desc = f"Business timestamp or operational date for {col_name.replace('_', ' ')}"
        elif pd.api.types.is_numeric_dtype(series.dtype):
            inferred_role = "metric"
            stats["min"] = float(valid_series.min()) if len(valid_series) > 0 else 0.0
            stats["max"] = float(valid_series.max()) if len(valid_series) > 0 else 0.0
            stats["mean"] = round(float(valid_series.mean()), 2) if len(valid_series) > 0 else 0.0
            stats["median"] = round(float(valid_series.median()), 2) if len(valid_series) > 0 else 0.0
            stats["std"] = round(float(valid_series.std()), 2) if len(valid_series) > 1 else 0.0
            inferred_desc = f"Operational numeric measure ranging from {stats['min']} to {stats['max']}"
        else:
            inferred_role = "text"
            inferred_desc = f"Textual or descriptive details for {col_name.replace('_', ' ')}"

        return {
            "column_name": col_name,
            "data_type": dtype_str,
            "inferred_role": inferred_role,
            "inferred_description": inferred_desc,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": unique_count,
            "sample_values": clean_samples,
            "is_primary_key": is_pk,
            "is_foreign_key": is_fk,
            "is_sensitive": is_sensitive,
            "stats": stats
        }

    @classmethod
    def detect_table_entity(cls, table_name: str, column_names: List[str]) -> Tuple[str, float, str]:
        table_lower = table_name.lower()
        cols_lower = [c.lower() for c in column_names]

        # 1. Exact or partial table name match
        for entity, keywords in ENTITY_DEFINITIONS.items():
            if entity.lower() in table_lower or table_lower in entity.lower():
                return entity, 0.95, f"Matched entity name '{entity}' from table '{table_name}'"

        # 2. Match based on characteristic column overlaps
        best_entity = "Custom Entity"
        best_score = 0.0
        best_match_col = ""

        for entity, keywords in ENTITY_DEFINITIONS.items():
            matches = [k for k in keywords if k in cols_lower]
            if matches:
                score = len(matches) / len(keywords)
                if score > best_score:
                    best_score = score
                    best_entity = entity
                    best_match_col = ", ".join(matches)

        if best_score > 0.2:
            conf = round(min(0.6 + best_score * 0.4, 0.92), 2)
            return best_entity, conf, f"Inferred '{best_entity}' based on columns: {best_match_col}"

        return "Operations Data", 0.50, "Generic operational table structure"

    @classmethod
    def profile_all_tables(cls, workspace_id: Optional[str], db: Session) -> List[Dict[str, Any]]:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
        if not ws:
            return []

        from backend.services.warehouse import get_warehouse_tables
        wh_tables = get_warehouse_tables()
        existing_names = {t.table_name for t in db.query(DataSourceTable).all()}
        missing = [t for t in wh_tables if t not in existing_names]
        if missing:
            ds = db.query(DataSource).filter(DataSource.workspace_id == ws.id, DataSource.name == "Operational Warehouse").first()
            if not ds:
                ds = DataSource(workspace_id=ws.id, name="Operational Warehouse", source_type="sqlite", status="connected")
                db.add(ds)
                db.flush()
            for m in missing:
                db.add(DataSourceTable(data_source_id=ds.id, table_name=m, row_count=0, column_count=0))
            db.commit()

        tables = db.query(DataSourceTable).join(DataSource).filter(DataSource.workspace_id == ws.id).all()
        profiles = []

        for tbl in tables:
            # Query table data from warehouse
            try:
                df = query_warehouse(f'SELECT * FROM "{tbl.table_name}"')
            except Exception:
                continue

            tbl.row_count = len(df)
            tbl.column_count = len(df.columns)

            missing_cells = int(df.isnull().sum().sum())
            duplicate_rows = int(df.duplicated().sum())
            entity_name, entity_conf, entity_reason = cls.detect_table_entity(tbl.table_name, list(df.columns))

            col_profiles = []
            for col in df.columns:
                cp = cls.profile_column(df[col], col, tbl.table_name)
                col_profiles.append(cp)

                # Persist or update in DataCatalogColumn
                existing_col = (
                    db.query(DataCatalogColumn)
                    .filter(DataCatalogColumn.table_id == tbl.id, DataCatalogColumn.column_name == col)
                    .first()
                )
                if not existing_col:
                    new_col = DataCatalogColumn(
                        table_id=tbl.id,
                        column_name=col,
                        data_type=cp["data_type"],
                        inferred_role=cp["inferred_role"],
                        inferred_description=cp["inferred_description"],
                        null_count=cp["null_count"],
                        null_percentage=cp["null_percentage"],
                        unique_count=cp["unique_count"],
                        sample_values=cp["sample_values"],
                        is_primary_key=cp["is_primary_key"],
                        is_foreign_key=cp["is_foreign_key"],
                        is_sensitive=cp["is_sensitive"]
                    )
                    db.add(new_col)
                else:
                    existing_col.data_type = cp["data_type"]
                    existing_col.inferred_role = cp["inferred_role"]
                    existing_col.inferred_description = cp["inferred_description"]
                    existing_col.null_count = cp["null_count"]
                    existing_col.null_percentage = cp["null_percentage"]
                    existing_col.unique_count = cp["unique_count"]
                    existing_col.sample_values = cp["sample_values"]
                    existing_col.is_primary_key = cp["is_primary_key"]
                    existing_col.is_foreign_key = cp["is_foreign_key"]
                    existing_col.is_sensitive = cp["is_sensitive"]

            # Save schema metadata with entity info
            tbl.schema_metadata = {
                "detected_entity": entity_name,
                "entity_confidence": entity_conf,
                "entity_reason": entity_reason,
                "missing_cells_total": missing_cells,
                "duplicate_rows": duplicate_rows
            }

            profiles.append({
                "id": tbl.id,
                "table_name": tbl.table_name,
                "row_count": tbl.row_count,
                "column_count": tbl.column_count,
                "missing_cells_total": missing_cells,
                "duplicate_rows": duplicate_rows,
                "detected_entity": entity_name,
                "columns": col_profiles
            })

        db.commit()
        # Automatically discover relationships across newly profiled tables
        cls.discover_relationships(ws.id, db)
        return profiles

    @classmethod
    def profile_table(cls, db: Session, table_id: str) -> Optional[Dict[str, Any]]:
        tbl = db.query(DataSourceTable).filter(DataSourceTable.id == table_id).first()
        if not tbl:
            return None
        try:
            df = query_warehouse(f'SELECT * FROM "{tbl.table_name}"')
        except Exception:
            return None

        tbl.row_count = len(df)
        tbl.column_count = len(df.columns)
        missing_cells = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        entity_name, entity_conf, entity_reason = cls.detect_table_entity(tbl.table_name, list(df.columns))

        col_profiles = []
        for col in df.columns:
            cp = cls.profile_column(df[col], col, tbl.table_name)
            col_profiles.append(cp)
            existing_col = (
                db.query(DataCatalogColumn)
                .filter(DataCatalogColumn.table_id == tbl.id, DataCatalogColumn.column_name == col)
                .first()
            )
            if not existing_col:
                new_col = DataCatalogColumn(
                    table_id=tbl.id,
                    column_name=col,
                    data_type=cp["data_type"],
                    inferred_role=cp["inferred_role"],
                    inferred_description=cp["inferred_description"],
                    null_count=cp["null_count"],
                    null_percentage=cp["null_percentage"],
                    unique_count=cp["unique_count"],
                    sample_values=cp["sample_values"],
                    is_primary_key=cp["is_primary_key"],
                    is_foreign_key=cp["is_foreign_key"],
                    is_sensitive=cp["is_sensitive"]
                )
                db.add(new_col)
            else:
                existing_col.data_type = cp["data_type"]
                existing_col.inferred_role = cp["inferred_role"]
                existing_col.null_count = cp["null_count"]
                existing_col.null_percentage = cp["null_percentage"]
                existing_col.unique_count = cp["unique_count"]
                existing_col.sample_values = cp["sample_values"]
                existing_col.is_primary_key = cp["is_primary_key"]
                existing_col.is_foreign_key = cp["is_foreign_key"]
                existing_col.is_sensitive = cp["is_sensitive"]

        tbl.schema_metadata = {
            "detected_entity": entity_name,
            "entity_confidence": entity_conf,
            "entity_reason": entity_reason,
            "missing_cells_total": missing_cells,
            "duplicate_rows": duplicate_rows
        }
        db.commit()
        return tbl.schema_metadata


    @classmethod
    def discover_relationships(cls, workspace_id: str, db: Session) -> List[Relationship]:
        tables = (
            db.query(DataSourceTable)
            .join(DataSource)
            .filter(DataSource.workspace_id == workspace_id)
            .all()
        )
        
        discovered = []
        table_cols = {}
        for t in tables:
            cols = db.query(DataCatalogColumn).filter(DataCatalogColumn.table_id == t.id).all()
            table_cols[t.table_name] = {c.column_name: c for c in cols}

        table_names = list(table_cols.keys())
        for i in range(len(table_names)):
            for j in range(len(table_names)):
                if i == j:
                    continue
                src_tbl = table_names[i]
                tgt_tbl = table_names[j]

                for src_col, src_meta in table_cols[src_tbl].items():
                    # Look for foreign key matching target primary key
                    # e.g., orders.customer_id -> customers.customer_id
                    for tgt_col, tgt_meta in table_cols[tgt_tbl].items():
                        match = False
                        confidence = 0.0

                        # Case 1: Same column name ending in _id
                        if src_col == tgt_col and src_col.endswith("_id"):
                            match = True
                            confidence = 0.90
                        # Case 2: Target column is 'id' and source column is '<target_single>_id'
                        elif tgt_col == "id" and src_col == f"{tgt_tbl.rstrip('s')}_id":
                            match = True
                            confidence = 0.85
                        # Case 3: Target table singular matches prefix of source col
                        elif src_col == f"{tgt_tbl.rstrip('s')}_{tgt_col}":
                            match = True
                            confidence = 0.85

                        if match:
                            # Verify value overlap in warehouse
                            try:
                                q = f"""
                                    SELECT 
                                        COUNT(DISTINCT a."{src_col}") AS src_distinct,
                                        COUNT(DISTINCT CASE WHEN b."{tgt_col}" IS NOT NULL THEN a."{src_col}" END) AS overlap
                                    FROM "{src_tbl}" a
                                    LEFT JOIN "{tgt_tbl}" b ON a."{src_col}" = b."{tgt_col}"
                                    WHERE a."{src_col}" IS NOT NULL
                                """
                                res = query_warehouse(q)
                                if len(res) > 0 and res["src_distinct"].iloc[0] > 0:
                                    src_dist = float(res["src_distinct"].iloc[0])
                                    overlap_count = float(res["overlap"].iloc[0])
                                    overlap_ratio = overlap_count / src_dist
                                    if overlap_ratio >= 0.95:
                                        confidence = min(0.98, confidence + 0.08)
                                    elif overlap_ratio >= 0.5:
                                        confidence = round(confidence * overlap_ratio, 2)
                                    else:
                                        # Very low overlap, decrease confidence
                                        confidence = round(confidence * 0.5, 2)
                            except Exception:
                                pass

                            # Check if relationship already exists
                            rel = (
                                db.query(Relationship)
                                .filter(
                                    Relationship.workspace_id == workspace_id,
                                    Relationship.source_table_name == src_tbl,
                                    Relationship.source_column_name == src_col,
                                    Relationship.target_table_name == tgt_tbl,
                                    Relationship.target_column_name == tgt_col
                                )
                                .first()
                            )
                            if not rel:
                                rel = Relationship(
                                    workspace_id=workspace_id,
                                    source_table_name=src_tbl,
                                    source_column_name=src_col,
                                    target_table_name=tgt_tbl,
                                    target_column_name=tgt_col,
                                    confidence_score=confidence,
                                    detection_method="schema_and_value_overlap",
                                    is_verified=True if confidence >= 0.8 else False
                                )
                                db.add(rel)
                                discovered.append(rel)
                            else:
                                rel.confidence_score = confidence
                                discovered.append(rel)

        db.commit()
        return discovered
