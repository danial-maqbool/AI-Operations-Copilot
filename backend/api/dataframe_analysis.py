from fastapi import APIRouter, HTTPException
from backend.schemas.dataframe_analysis import (
    GroupByRequest, PivotRequest, CorrelationRequest,
    RollingRequest, TimeSeriesRequest, AnalysisResult
)
from backend.services.dataframe_service import DataFrameAnalysisService

router = APIRouter(prefix="/analysis", tags=["DataFrame Analysis Engine"])

@router.post("/groupby", response_model=AnalysisResult)
def group_by(req: GroupByRequest):
    try:
        return DataFrameAnalysisService.group_by_analysis(req.table_name, req.group_cols, req.aggregations)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pivot", response_model=AnalysisResult)
def pivot(req: PivotRequest):
    try:
        return DataFrameAnalysisService.pivot_analysis(req.table_name, req.index_col, req.columns_col, req.values_col, req.agg_func)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/correlation", response_model=AnalysisResult)
def correlation(req: CorrelationRequest):
    try:
        return DataFrameAnalysisService.correlation_analysis(req.table_name, req.numeric_cols)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rolling", response_model=AnalysisResult)
def rolling(req: RollingRequest):
    try:
        return DataFrameAnalysisService.rolling_averages(req.table_name, req.date_col, req.value_col, req.window)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/timeseries", response_model=AnalysisResult)
def timeseries(req: TimeSeriesRequest):
    try:
        return DataFrameAnalysisService.time_series_aggregation(req.table_name, req.date_col, req.value_col, req.frequency, req.agg_func)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
