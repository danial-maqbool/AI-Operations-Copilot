from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "OpsPilot - AI Operations Copilot",
        "version": "1.0.0",
        "ai_enabled": settings.AI_ENABLED,
        "model": settings.GEMINI_MODEL,
    }
