from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

from backend.services.entity_views import EntityViewService

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("/customer/{customer_id}")
def get_customer_360(customer_id: str):
    """
    Returns 360 operational view of a customer (orders, overdue invoices, support tickets, health score).
    """
    try:
        return EntityViewService.get_customer_360(customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer 360: {str(e)}")

@router.get("/order/{order_id}")
def get_order_360(order_id: str):
    """
    Returns 360 operational view of an order (items, shipping tracking, delay analysis, invoices).
    """
    try:
        return EntityViewService.get_order_360(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order 360: {str(e)}")

@router.get("/sla-monitor")
def get_sla_risk_monitor():
    """
    Returns comprehensive SLA monitor across orders, support tickets, and payments.
    """
    try:
        return EntityViewService.get_sla_risk_monitor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SLA monitor: {str(e)}")
