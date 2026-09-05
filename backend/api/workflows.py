from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowRunResponse
)
from backend.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("", response_model=List[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db)):
    """
    Returns all defined operational workflows.
    """
    return WorkflowService.list_workflows(db)

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    """
    Creates a new operational workflow definition.
    """
    return WorkflowService.create_workflow(db, payload)

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = WorkflowService.get_workflow(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: Session = Depends(get_db)):
    wf = WorkflowService.update_workflow(db, workflow_id, payload)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    success = WorkflowService.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return None

@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
def trigger_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Triggers execution of an operational workflow.
    """
    try:
        return WorkflowService.run_workflow(db, workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
