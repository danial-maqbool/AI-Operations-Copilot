import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.ensemble import IsolationForest

from backend.services.warehouse import query_warehouse
from backend.schemas.anomaly import AnomalyItem, AnomalyScanResponse

class AnomalyDetectionService:
    @classmethod
    def detect_zscore(cls, df: pd.DataFrame, col_name: str, table_name: str, threshold: float = 3.0) -> List[AnomalyItem]:
        s = pd.to_numeric(df[col_name], errors="coerce").dropna()
        if len(s) < 5:
            return []

        mean_val = float(s.mean())
        std_val = float(s.std())
        if std_val == 0.0:
            return []

        min_expected = round(mean_val - (threshold * std_val), 2)
        max_expected = round(mean_val + (threshold * std_val), 2)

        id_col = [c for c in df.columns if c.endswith("_id") or c == "id"]
        date_col = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

        anomalies = []
        for idx, val in s.items():
            z = (val - mean_val) / std_val
            if abs(z) >= threshold:
                dev = round(val - mean_val, 2)
                dev_pct = round((dev / abs(mean_val)) * 100, 2) if mean_val != 0 else 0.0
                rec_id = str(df.loc[idx, id_col[0]]) if id_col else str(idx)
                dt_str = str(df.loc[idx, date_col[0]]) if date_col and pd.notnull(df.loc[idx, date_col[0]]) else None

                drivers = [
                    f"[Hypothesis] Statistical deviation of {z:.1f} standard deviations from mean ({mean_val:.1f})",
                    "[Hypothesis] Unusually large transaction volume or outlier input data"
                ]

                anomalies.append(AnomalyItem(
                    table_name=table_name,
                    column_name=col_name,
                    method="z_score",
                    observed_value=round(float(val), 2),
                    expected_range={"min": min_expected, "max": max_expected},
                    deviation=dev,
                    deviation_percentage=dev_pct,
                    record_id=rec_id,
                    date=dt_str,
                    potential_drivers=drivers,
                    is_verified_impact=False,
                    details={"z_score": round(float(z), 2), "mean": round(mean_val, 2), "std": round(std_val, 2)}
                ))
        return anomalies

    @classmethod
    def detect_iqr(cls, df: pd.DataFrame, col_name: str, table_name: str, multiplier: float = 1.5) -> List[AnomalyItem]:
        s = pd.to_numeric(df[col_name], errors="coerce").dropna()
        if len(s) < 5:
            return []

        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0:
            return []

        lower_bound = round(q1 - (multiplier * iqr), 2)
        upper_bound = round(q3 + (multiplier * iqr), 2)

        id_col = [c for c in df.columns if c.endswith("_id") or c == "id"]
        date_col = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

        anomalies = []
        for idx, val in s.items():
            if val < lower_bound or val > upper_bound:
                dev = round(val - q3 if val > upper_bound else val - q1, 2)
                rec_id = str(df.loc[idx, id_col[0]]) if id_col else str(idx)
                dt_str = str(df.loc[idx, date_col[0]]) if date_col and pd.notnull(df.loc[idx, date_col[0]]) else None

                drivers = [
                    f"[Hypothesis] Outside IQR boundary [{lower_bound}, {upper_bound}]",
                    "[Hypothesis] Potential skew from customer tier or unusual operational shift"
                ]

                anomalies.append(AnomalyItem(
                    table_name=table_name,
                    column_name=col_name,
                    method="iqr",
                    observed_value=round(float(val), 2),
                    expected_range={"min": lower_bound, "max": upper_bound},
                    deviation=dev,
                    deviation_percentage=round((dev / abs(q3 or 1.0)) * 100, 2),
                    record_id=rec_id,
                    date=dt_str,
                    potential_drivers=drivers,
                    is_verified_impact=False,
                    details={"q1": round(q1, 2), "q3": round(q3, 2), "iqr": round(iqr, 2)}
                ))
        return anomalies

    @classmethod
    def detect_rolling_deviation(cls, df: pd.DataFrame, val_col: str, date_col: str, table_name: str, window: int = 7) -> List[AnomalyItem]:
        if date_col not in df.columns or val_col not in df.columns:
            return []

        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
        temp_df[val_col] = pd.to_numeric(temp_df[val_col], errors="coerce")
        clean = temp_df.dropna(subset=[date_col, val_col]).sort_values(by=date_col)
        if len(clean) < window * 2:
            return []

        clean["rolling_mean"] = clean[val_col].shift(1).rolling(window=window, min_periods=3).mean()
        clean["rolling_std"] = clean[val_col].shift(1).rolling(window=window, min_periods=3).std()

        id_col = [c for c in df.columns if c.endswith("_id") or c == "id"]
        anomalies = []

        for idx, row in clean.iterrows():
            r_mean = row["rolling_mean"]
            r_std = row["rolling_std"]
            val = row[val_col]
            if pd.notnull(r_mean) and pd.notnull(r_std) and r_std > 0:
                diff = abs(val - r_mean)
                if diff > (2.5 * r_std):
                    rec_id = str(row[id_col[0]]) if id_col else str(idx)
                    anomalies.append(AnomalyItem(
                        table_name=table_name,
                        column_name=val_col,
                        method="rolling_deviation",
                        observed_value=round(float(val), 2),
                        expected_range={
                            "min": round(float(r_mean - 2 * r_std), 2),
                            "max": round(float(r_mean + 2 * r_std), 2)
                        },
                        deviation=round(float(val - r_mean), 2),
                        deviation_percentage=round((float(val - r_mean) / abs(float(r_mean or 1))) * 100, 2),
                        record_id=rec_id,
                        date=str(row[date_col])[:10],
                        potential_drivers=[
                            f"[Hypothesis] Exceeds 7-day moving trend average by {diff/r_std:.1f}x standard deviation",
                            "[Hypothesis] Abrupt demand surge, supply disruption, or reporting delay"
                        ],
                        is_verified_impact=False,
                        details={"rolling_mean": round(float(r_mean), 2), "rolling_std": round(float(r_std), 2)}
                    ))
        return anomalies

    @classmethod
    def detect_isolation_forest(cls, df: pd.DataFrame, numeric_cols: List[str], table_name: str) -> List[AnomalyItem]:
        num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce").dropna()
        if len(num_df) < 15 or len(numeric_cols) == 0:
            return []

        try:
            iso = IsolationForest(contamination=0.05, random_state=42)
            preds = iso.fit_predict(num_df)
            scores = iso.score_samples(num_df)
            outlier_indices = num_df.index[preds == -1]

            id_col = [c for c in df.columns if c.endswith("_id") or c == "id"]
            date_col = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

            anomalies = []
            for idx in outlier_indices:
                rec_id = str(df.loc[idx, id_col[0]]) if id_col else str(idx)
                dt_str = str(df.loc[idx, date_col[0]]) if date_col and pd.notnull(df.loc[idx, date_col[0]]) else None
                top_col = numeric_cols[0]
                val = float(num_df.loc[idx, top_col])
                mean_v = float(num_df[top_col].mean())

                anomalies.append(AnomalyItem(
                    table_name=table_name,
                    column_name=top_col,
                    method="isolation_forest",
                    observed_value=round(val, 2),
                    expected_range={"min": round(mean_v * 0.5, 2), "max": round(mean_v * 1.5, 2)},
                    deviation=round(val - mean_v, 2),
                    deviation_percentage=round(((val - mean_v) / abs(mean_v or 1)) * 100, 2),
                    record_id=rec_id,
                    date=dt_str,
                    potential_drivers=[
                        "[Hypothesis] Multi-dimensional anomaly detected via Isolation Forest",
                        "[Hypothesis] Atypical combination of numeric attributes across transaction"
                    ],
                    is_verified_impact=False,
                    details={"anomaly_score": round(float(scores[num_df.index.get_loc(idx)]), 3)}
                ))
            return anomalies
        except Exception:
            return []

    @classmethod
    def scan_table(cls, table_name: str, columns: Optional[List[str]] = None, method: str = "all", threshold: float = 3.0) -> AnomalyScanResponse:
        df = query_warehouse(f'SELECT * FROM "{table_name}"')
        if df.empty:
            return AnomalyScanResponse(table_name=table_name, total_records_analyzed=0, anomalies_detected=0, items=[])

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        target_cols = [c for c in (columns or num_cols) if c in num_cols and not c.endswith("_id") and c != "id"]

        date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

        items: List[AnomalyItem] = []

        for col in target_cols:
            if method in ["all", "z_score"]:
                items.extend(cls.detect_zscore(df, col, table_name, threshold=threshold))
            if method in ["all", "iqr"]:
                items.extend(cls.detect_iqr(df, col, table_name))
            if method in ["all", "rolling"] and date_cols:
                items.extend(cls.detect_rolling_deviation(df, col, date_cols[0], table_name))

        if method in ["all", "isolation_forest"] and len(target_cols) >= 2:
            items.extend(cls.detect_isolation_forest(df, target_cols, table_name))

        # De-duplicate items by record_id + column_name
        seen = set()
        deduped = []
        for it in items:
            key = (it.table_name, it.column_name, it.record_id, it.method)
            if key not in seen:
                seen.add(key)
                deduped.append(it)

        return AnomalyScanResponse(
            table_name=table_name,
            total_records_analyzed=len(df),
            anomalies_detected=len(deduped),
            items=deduped
        )

    @classmethod
    def detect_table_anomalies(cls, table_name: str) -> Dict[str, Any]:
        res = cls.scan_table(table_name)
        return {
            "table_name": table_name,
            "total_anomalies": res.anomalies_detected,
            "anomalies": [
                {
                    "column": it.column_name,
                    "outlier_value": it.observed_value,
                    "method": it.method,
                    "deviation_score": it.deviation
                } for it in res.items
            ]
        }

AnomalyService = AnomalyDetectionService

