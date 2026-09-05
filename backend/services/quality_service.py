import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import DataSourceTable, DataCatalogColumn, Relationship, Workspace, DataSource
from backend.services.warehouse import query_warehouse
from backend.schemas.quality import (
    QualityFinding, ComponentHealthScore, TableQualityReport, WorkspaceQualitySummary
)

NON_NEGATIVE_KEYWORDS = ["price", "cost", "amount", "quantity", "qty", "stock", "balance", "total", "revenue"]
PERCENTAGE_KEYWORDS = ["pct", "percent", "percentage", "rate", "ratio", "margin"]

class DataQualityEngine:
    @classmethod
    def audit_table(cls, table_name: str, cols: List[DataCatalogColumn]) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        try:
            df = query_warehouse(f'SELECT * FROM "{table_name}"')
        except Exception as e:
            return {
                "table_name": table_name,
                "row_count": 0,
                "health_score": 0.0,
                "component_scores": {
                    "completeness": 0.0, "uniqueness": 0.0, "validity": 0.0,
                    "consistency": 0.0, "referential_integrity": 100.0,
                    "overall_score": 0.0, "formula_explanation": f"Failed to read table: {str(e)}"
                },
                "findings": []
            }

        total_rows = len(df)
        if total_rows == 0:
            return {
                "table_name": table_name,
                "row_count": 0,
                "health_score": 100.0,
                "component_scores": {
                    "completeness": 100.0, "uniqueness": 100.0, "validity": 100.0,
                    "consistency": 100.0, "referential_integrity": 100.0,
                    "overall_score": 100.0, "formula_explanation": "Empty table"
                },
                "findings": []
            }

        col_dict = {c.column_name: c for c in cols}

        # 1. Check Missing Values & Primary Key Nulls
        pk_cols = [c.column_name for c in cols if c.is_primary_key]
        for col_name in df.columns:
            null_count = int(df[col_name].isnull().sum())
            if null_count > 0:
                pct = round((null_count / total_rows) * 100, 2)
                is_pk = col_name in pk_cols
                sev = "CRITICAL" if is_pk else ("WARNING" if pct > 20.0 else "INFO")
                desc = f"Primary key '{col_name}' contains unexpected nulls!" if is_pk else f"Column '{col_name}' has {null_count} missing values ({pct}%)"
                findings.append({
                    "table_name": table_name,
                    "column_name": col_name,
                    "finding_type": "unexpected_null_pk" if is_pk else "missing_value",
                    "severity": sev,
                    "description": desc,
                    "affected_count": null_count,
                    "affected_percentage": pct,
                    "evidence_samples": []
                })

        # 2. Check Duplicate Identifiers (PK uniqueness)
        for pk in pk_cols:
            if pk in df.columns:
                dups = int(df[pk].duplicated().sum())
                if dups > 0:
                    pct = round((dups / total_rows) * 100, 2)
                    dup_vals = df[df[pk].duplicated(keep=False)][pk].head(5).tolist()
                    findings.append({
                        "table_name": table_name,
                        "column_name": pk,
                        "finding_type": "duplicate_pk",
                        "severity": "CRITICAL",
                        "description": f"Primary key column '{pk}' has {dups} duplicate values violating uniqueness ({pct}%)",
                        "affected_count": dups,
                        "affected_percentage": pct,
                        "evidence_samples": [str(x) for x in dup_vals]
                    })

        # 3. Check Duplicate Entire Rows
        dup_rows = int(df.duplicated().sum())
        if dup_rows > 0:
            pct = round((dup_rows / total_rows) * 100, 2)
            findings.append({
                "table_name": table_name,
                "column_name": None,
                "finding_type": "duplicate_row",
                "severity": "WARNING",
                "description": f"Table has {dup_rows} identical duplicate rows ({pct}%)",
                "affected_count": dup_rows,
                "affected_percentage": pct,
                "evidence_samples": []
            })

        # 4. Check Negative Values in naturally non-negative columns
        for col_name in df.columns:
            if any(kw in col_name.lower() for kw in NON_NEGATIVE_KEYWORDS):
                if pd.api.types.is_numeric_dtype(df[col_name].dtype):
                    neg_mask = df[col_name] < 0
                    neg_count = int(neg_mask.sum())
                    if neg_count > 0:
                        pct = round((neg_count / total_rows) * 100, 2)
                        samples = df[neg_mask][col_name].head(5).tolist()
                        findings.append({
                            "table_name": table_name,
                            "column_name": col_name,
                            "finding_type": "negative_value",
                            "severity": "CRITICAL" if "stock" in col_name.lower() or "price" in col_name.lower() else "WARNING",
                            "description": f"Column '{col_name}' has {neg_count} unexpected negative values",
                            "affected_count": neg_count,
                            "affected_percentage": pct,
                            "evidence_samples": [float(x) for x in samples]
                        })

        # 5. Check Impossible Percentages
        for col_name in df.columns:
            if any(kw in col_name.lower() for kw in PERCENTAGE_KEYWORDS) and "amount" not in col_name.lower():
                if pd.api.types.is_numeric_dtype(df[col_name].dtype):
                    # Percentages could be 0.0-1.0 or 0-100
                    s = df[col_name].dropna()
                    if len(s) > 0:
                        # If values exceed 1.0, assumed 0-100 scale
                        is_100_scale = float(s.max()) > 1.0
                        limit = 100.0 if is_100_scale else 1.0
                        bad_mask = (df[col_name] < 0) | (df[col_name] > limit)
                        bad_count = int(bad_mask.sum())
                        if bad_count > 0:
                            pct = round((bad_count / total_rows) * 100, 2)
                            samples = df[bad_mask][col_name].head(5).tolist()
                            findings.append({
                                "table_name": table_name,
                                "column_name": col_name,
                                "finding_type": "impossible_pct",
                                "severity": "WARNING",
                                "description": f"Column '{col_name}' has {bad_count} impossible percentage values outside [0, {limit}]",
                                "affected_count": bad_count,
                                "affected_percentage": pct,
                                "evidence_samples": [float(x) for x in samples]
                            })

        # 6. Check Inconsistent Categories (casing or trailing space discrepancies)
        for col_name in df.columns:
            if pd.api.types.is_string_dtype(df[col_name].dtype) or "str" in str(df[col_name].dtype).lower() or "object" in str(df[col_name].dtype).lower():
                s = df[col_name].dropna().astype(str)
                if 2 <= s.nunique() <= 30:
                    raw_vals = s.unique().tolist()
                    norm_map = {}
                    for v in raw_vals:
                        norm = v.strip().lower()
                        norm_map.setdefault(norm, []).append(v)
                    inconsistent = {k: v for k, v in norm_map.items() if len(v) > 1}
                    if inconsistent:
                        incons_samples = []
                        for k, v in inconsistent.items():
                            incons_samples.append(f"{v} -> '{k}'")
                        findings.append({
                            "table_name": table_name,
                            "column_name": col_name,
                            "finding_type": "inconsistent_category",
                            "severity": "WARNING",
                            "description": f"Column '{col_name}' has inconsistent category casing or spacing: {', '.join(incons_samples[:3])}",
                            "affected_count": len(inconsistent),
                            "affected_percentage": round((len(inconsistent) / len(raw_vals)) * 100, 2),
                            "evidence_samples": incons_samples[:5]
                        })

        # 7. Check Invalid / Out-of-bounds Dates
        for col_name in df.columns:
            if "date" in col_name.lower() or "time" in col_name.lower():
                if pd.api.types.is_string_dtype(df[col_name].dtype) or "str" in str(df[col_name].dtype).lower() or "object" in str(df[col_name].dtype).lower():
                    s = df[col_name].dropna().astype(str)
                    parsed = pd.to_datetime(s, errors="coerce")
                    invalid_cnt = int(parsed.isna().sum())
                    if invalid_cnt > 0:
                        pct = round((invalid_cnt / total_rows) * 100, 2)
                        bad_samples = s[parsed.isna()].head(5).tolist()
                        findings.append({
                            "table_name": table_name,
                            "column_name": col_name,
                            "finding_type": "invalid_date",
                            "severity": "WARNING",
                            "description": f"Column '{col_name}' has {invalid_cnt} unparseable or invalid date values",
                            "affected_count": invalid_cnt,
                            "affected_percentage": pct,
                            "evidence_samples": bad_samples
                        })

        return {
            "table_name": table_name,
            "row_count": total_rows,
            "findings": findings
        }

    @classmethod
    def check_referential_integrity(cls, workspace_id: str, db: Session) -> List[Dict[str, Any]]:
        relationships = db.query(Relationship).filter(Relationship.workspace_id == workspace_id).all()
        ref_findings = []

        for rel in relationships:
            src_tbl = rel.source_table_name
            src_col = rel.source_column_name
            tgt_tbl = rel.target_table_name
            tgt_col = rel.target_column_name

            sql = f"""
                SELECT COUNT(*) as orphaned_count
                FROM "{src_tbl}" a
                WHERE a."{src_col}" IS NOT NULL 
                  AND a."{src_col}" NOT IN (SELECT b."{tgt_col}" FROM "{tgt_tbl}" b WHERE b."{tgt_col}" IS NOT NULL)
            """
            try:
                res = query_warehouse(sql)
                orphaned = int(res["orphaned_count"].iloc[0])
                if orphaned > 0:
                    tot_res = query_warehouse(f'SELECT COUNT(*) as total FROM "{src_tbl}" WHERE "{src_col}" IS NOT NULL')
                    total_src = int(tot_res["total"].iloc[0]) if len(tot_res) > 0 else 1
                    pct = round((orphaned / max(total_src, 1)) * 100, 2)

                    # Get orphaned samples
                    sample_sql = f"""
                        SELECT DISTINCT a."{src_col}"
                        FROM "{src_tbl}" a
                        WHERE a."{src_col}" IS NOT NULL 
                          AND a."{src_col}" NOT IN (SELECT b."{tgt_col}" FROM "{tgt_tbl}" b WHERE b."{tgt_col}" IS NOT NULL)
                        LIMIT 5
                    """
                    samples_df = query_warehouse(sample_sql)
                    sample_vals = [str(x) for x in samples_df[src_col].tolist()]

                    ref_findings.append({
                        "table_name": src_tbl,
                        "column_name": src_col,
                        "finding_type": "orphaned_fk",
                        "severity": "CRITICAL",
                        "description": f"Found {orphaned} orphaned foreign keys in '{src_tbl}.{src_col}' referencing non-existent '{tgt_tbl}.{tgt_col}' ({pct}%)",
                        "affected_count": orphaned,
                        "affected_percentage": pct,
                        "evidence_samples": sample_vals
                    })
            except Exception:
                pass

        return ref_findings

    @classmethod
    def calculate_health_scores(cls, findings: List[Dict[str, Any]], total_rows: int, total_cols: int) -> ComponentHealthScore:
        total_cells = max(total_rows * max(total_cols, 1), 1)

        # 1. Completeness: 100 - % null cells
        null_cells = sum(f["affected_count"] for f in findings if f["finding_type"] in ["missing_value", "unexpected_null_pk"])
        completeness = max(0.0, min(100.0, round(100.0 - (null_cells / total_cells * 100), 1)))

        # 2. Uniqueness: 100 - % duplicate rows & PK collisions
        dup_cells = sum(f["affected_count"] for f in findings if f["finding_type"] in ["duplicate_pk", "duplicate_row"])
        uniqueness = max(0.0, min(100.0, round(100.0 - (dup_cells / max(total_rows, 1) * 100), 1)))

        # 3. Validity: 100 - % negative values, invalid dates, impossible percentages
        invalid_cells = sum(f["affected_count"] for f in findings if f["finding_type"] in ["negative_value", "invalid_date", "impossible_pct"])
        validity = max(0.0, min(100.0, round(100.0 - (invalid_cells / max(total_rows, 1) * 100), 1)))

        # 4. Consistency: 100 - penalty for inconsistent categories
        inconsistent_findings = [f for f in findings if f["finding_type"] == "inconsistent_category"]
        consistency = max(0.0, min(100.0, round(100.0 - (len(inconsistent_findings) * 5.0), 1)))

        # 5. Referential Integrity: 100 - % orphaned FK records
        orphaned_cells = sum(f["affected_count"] for f in findings if f["finding_type"] == "orphaned_fk")
        referential = max(0.0, min(100.0, round(100.0 - (orphaned_cells / max(total_rows, 1) * 100), 1)))

        # Weighted calculation
        overall = round(
            (completeness * 0.25) +
            (uniqueness * 0.20) +
            (validity * 0.20) +
            (consistency * 0.15) +
            (referential * 0.20),
            1
        )

        explanation = (
            "OpsPilot Data Health Score Formula: (Completeness * 0.25) + (Uniqueness * 0.20) + "
            "(Validity * 0.20) + (Consistency * 0.15) + (Referential Integrity * 0.20). "
            "Application-specific composite quality index."
        )

        return ComponentHealthScore(
            completeness=completeness,
            uniqueness=uniqueness,
            validity=validity,
            consistency=consistency,
            referential_integrity=referential,
            overall_score=overall,
            formula_explanation=explanation
        )

    @classmethod
    def run_workspace_audit(cls, workspace_id: Optional[str], db: Session) -> WorkspaceQualitySummary:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first() if workspace_id else db.query(Workspace).first()
        if not ws:
            raise ValueError("No workspace found")

        tables = db.query(DataSourceTable).join(DataSource).filter(DataSource.workspace_id == ws.id).all()
        table_reports = []
        all_findings = []

        # Referential integrity across all tables
        ref_findings = cls.check_referential_integrity(ws.id, db)
        ref_by_table = {}
        for rf in ref_findings:
            ref_by_table.setdefault(rf["table_name"], []).append(rf)

        for tbl in tables:
            cols = db.query(DataCatalogColumn).filter(DataCatalogColumn.table_id == tbl.id).all()
            res = cls.audit_table(tbl.table_name, cols)
            
            # Combine with table's referential findings
            tbl_findings = res["findings"] + ref_by_table.get(tbl.table_name, [])
            all_findings.extend(tbl_findings)

            scores = cls.calculate_health_scores(tbl_findings, tbl.row_count, tbl.column_count)
            tbl.data_health_score = scores.overall_score
            tbl.health_metrics = {
                "completeness": scores.completeness,
                "uniqueness": scores.uniqueness,
                "validity": scores.validity,
                "consistency": scores.consistency,
                "referential_integrity": scores.referential_integrity,
                "overall_score": scores.overall_score,
                "findings_count": len(tbl_findings)
            }

            typed_findings = [QualityFinding(**f) for f in tbl_findings]
            table_reports.append(TableQualityReport(
                table_name=tbl.table_name,
                row_count=tbl.row_count,
                health_score=scores.overall_score,
                component_scores=scores,
                findings=typed_findings
            ))

        db.commit()

        overall_score = round(np.mean([t.health_score for t in table_reports]), 1) if table_reports else 100.0
        critical_count = sum(1 for f in all_findings if f.get("severity") == "CRITICAL")
        warning_count = sum(1 for f in all_findings if f.get("severity") == "WARNING")

        return WorkspaceQualitySummary(
            workspace_id=ws.id,
            overall_data_health_score=overall_score,
            total_findings=len(all_findings),
            critical_findings=critical_count,
            warning_findings=warning_count,
            table_reports=table_reports
        )
