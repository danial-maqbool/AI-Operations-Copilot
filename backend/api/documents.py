import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.config import settings
from backend.models import Document
from backend.schemas.document import DocumentResponse, SearchResult
from backend.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["RAG Knowledge Base"])

class SearchRequest(BaseModel):
    query: str
    workspace_id: Optional[str] = None
    top_k: int = 4

@router.get("", response_model=List[DocumentResponse])
def list_documents(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if workspace_id:
        query = query.filter(Document.workspace_id == workspace_id)
    return query.all()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ext = Path(file.filename).suffix.lower()
    allowed = [".pdf", ".docx", ".doc", ".txt", ".md"]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Allowed: {allowed}")

    target_path = settings.UPLOADS_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        doc = RAGService.ingest_document(target_path, file.filename, workspace_id, db)
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

@router.post("/search", response_model=List[SearchResult])
def search_knowledge_base(req: SearchRequest, db: Session = Depends(get_db)):
    try:
        return RAGService.search(req.query, req.workspace_id, db, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": document_id}

@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Source file not found on disk")

    updated = RAGService.ingest_document(file_path, doc.filename, doc.workspace_id, db)
    return updated
