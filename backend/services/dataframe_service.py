import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

from backend.services.warehouse import query_warehouse
from backend.schemas.dataframe_analysis import AnalysisResult

class DataFrameAnalysisService:
    @classmethod
    def get_clean_table_df(cls, table_name: str) -> pd.DataFrame:
        df = query_warehouse(f'SELECT * FROM "{table_name}"')
        return df

    @classmethod
    def group_by_analysis(cls, table_name: str, group_cols: List[str], aggregations: Dict[str, List[str]]) -> AnalysisResult:
        df = cls.get_clean_table_df(table_name)
        
        # Verify columns
        for c in group_cols:
            if c not in df.columns:
                raise ValueError(f"Group column '{c}' not found in table '{table_name}'")
        for col_name in aggregations.keys():
            if col_name not in df.columns:
                raise ValueError(f"Aggregation target column '{col_name}' not found in table '{table_name}'")

        grouped = df.groupby(group_cols).agg(aggregations)
        
        # Flatten MultiIndex columns
        flat_cols = []
        for c in grouped.columns:
            if isinstance(c, tuple):
                flat_cols.append(f"{c[0]}_{c[1]}")
            else:
                flat_cols.append(str(c))
        grouped.columns = flat_cols
        res_df = grouped.reset_index()

        # Handle NaNs
        clean_res = res_df.where(pd.notnull(res_df), None)
        return AnalysisResult(
            operation="group_by",
            table_name=table_name,
            columns=list(clean_res.columns),
            rows=clean_res.to_dict(orient="records"),
            total_records=len(clean_res),
            summary_stats={
                "groups_count": len(clean_res),
                "grouped_by": group_cols
            }
        )

    @classmethod
    def pivot_analysis(cls, table_name: str, index_col: str, columns_col: str, values_col: str, agg_func: str = "sum") -> AnalysisResult:
        df = cls.get_clean_table_df(table_name)
        
        for col in [index_col, columns_col, values_col]:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in table '{table_name}'")

        pivot_df = pd.pivot_table(
            df,
            index=index_col,
            columns=columns_col,
            values=values_col,
            aggfunc=agg_func,
            fill_value=0
        ).reset_index()

        # Flatten column names
        pivot_df.columns = [str(c) for c in pivot_df.columns]
        clean_res = pivot_df.where(pd.notnull(pivot_df), None)

        return AnalysisResult(
            operation="pivot",
            table_name=table_name,
            columns=list(clean_res.columns),
            rows=clean_res.to_dict(orient="records"),
            total_records=len(clean_res),
            summary_stats={
                "index_field": index_col,
                "columns_field": columns_col,
                "values_field": values_col,
                "agg_func": agg_func
            }
        )

    @classmethod
    def correlation_analysis(cls, table_name: str, numeric_cols: Optional[List[str]] = None) -> AnalysisResult:
        df = cls.get_clean_table_df(table_name)
        
        # Select numeric columns
        if not numeric_cols:
            num_df = df.select_dtypes(include=[np.number])
        else:
            num_df = df[numeric_cols].select_dtypes(include=[np.number])

        if num_df.empty or len(num_df.columns) < 2:
            raise ValueError(f"Insufficient numeric columns in '{table_name}' to compute correlations")

        corr_matrix = num_df.corr().round(3).reset_index()
        corr_matrix.rename(columns={"index": "metric"}, inplace=True)
        clean_res = corr_matrix.where(pd.notnull(corr_matrix), 0.0)

        return AnalysisResult(
            operation="correlation",
            table_name=table_name,
            columns=list(clean_res.columns),
            rows=clean_res.to_dict(orient="records"),
            total_records=len(clean_res),
            summary_stats={"analyzed_metrics": list(num_df.columns)}
        )

    @classmethod
    def rolling_averages(cls, table_name: str, date_col: str, value_col: str, window: int = 7) -> AnalysisResult:
        df = cls.get_clean_table_df(table_name)
        if date_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"Columns '{date_col}' or '{value_col}' not found in '{table_name}'")

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df_sorted = df.dropna(subset=[date_col]).sort_values(by=date_col)
        df_sorted[f"{value_col}_rolling_avg_{window}"] = df_sorted[value_col].rolling(window=window, min_periods=1).mean().round(2)
        
        cols_to_keep = [date_col, value_col, f"{value_col}_rolling_avg_{window}"]
        res_df = df_sorted[cols_to_keep].copy()
        res_df[date_col] = res_df[date_col].dt.strftime("%Y-%m-%d")
        clean_res = res_df.where(pd.notnull(res_df), None)

        return AnalysisResult(
            operation="rolling_average",
            table_name=table_name,
            columns=list(clean_res.columns),
            rows=clean_res.to_dict(orient="records"),
            total_records=len(clean_res),
            summary_stats={"window": window, "value_col": value_col}
        )

    @classmethod
    def time_series_aggregation(cls, table_name: str, date_col: str, value_col: str, frequency: str = "D", agg_func: str = "sum") -> AnalysisResult:
        df = cls.get_clean_table_df(table_name)
        if date_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"Columns '{date_col}' or '{value_col}' not found in '{table_name}'")

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df_clean = df.dropna(subset=[date_col]).set_index(date_col)
        
        # Resample
        resampled = df_clean[value_col].resample(frequency).agg(agg_func).reset_index()
        resampled[date_col] = resampled[date_col].dt.strftime("%Y-%m-%d")
        resampled[value_col] = resampled[value_col].round(2)
        
        # Period-over-period change
        resampled["pct_change"] = resampled[value_col].pct_change().fillna(0).round(4) * 100.0

        clean_res = resampled.where(pd.notnull(resampled), 0)
        return AnalysisResult(
            operation="time_series_aggregation",
            table_name=table_name,
            columns=list(clean_res.columns),
            rows=clean_res.to_dict(orient="records"),
            total_records=len(clean_res),
            summary_stats={
                "frequency": frequency,
                "agg_func": agg_func,
                "total_periods": len(clean_res),
                "latest_value": float(clean_res[value_col].iloc[-1]) if len(clean_res) > 0 else 0.0
            }
        )
