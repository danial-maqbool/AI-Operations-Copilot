from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Conversation, Message
from backend.schemas.copilot import CopilotChatRequest, CopilotResponse
from backend.services.copilot_service import CopilotOrchestrator

router = APIRouter(prefix="/copilot", tags=["Operations Copilot Engine"])
orchestrator = CopilotOrchestrator()

@router.post("/chat", response_model=CopilotResponse)
def chat_with_copilot(req: CopilotChatRequest, db: Session = Depends(get_db)):
    try:
        return orchestrator.process_chat(req, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot processing failed: {str(e)}")

@router.get("/conversations")
def list_conversations(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Conversation)
    if workspace_id:
        q = q.filter(Conversation.workspace_id == workspace_id)
    return q.order_by(Conversation.updated_at.desc()).all()

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    return messages
