from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    page_number: int
    section_title: Optional[str] = None
    content: str
    relevance_score: float = 0.0

class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    file_type: str
    total_pages: int
    total_chunks: int
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    document_id: str
    filename: str
    page_number: int
    section_title: Optional[str] = None
    content: str
    score: float
    citation: str
