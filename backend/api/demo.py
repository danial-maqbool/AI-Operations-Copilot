from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database import get_db
from backend.services.demo_seed_service import DemoSeedService

router = APIRouter(prefix="/demo", tags=["Demo Company"])

@router.post("/load", status_code=status.HTTP_200_OK)
def load_demo_company(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Generates and loads the full 'Acme Industrial Supplies' demo dataset:
    - 10 operational tables (Customers, Products, Inventory, Orders, Order Items, Shipments, Invoices, Payments, Support Tickets, Employees)
    - 4 operational policy documents with full-text RAG indexing
    - Automatic column profiling & 5-dimension data quality score evaluation
    - Core operations KPIs with thresholds
    - Evaluated business rules generating prioritized exceptions
    """
    try:
        return DemoSeedService.generate_and_seed_demo_company(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo company: {str(e)}")
