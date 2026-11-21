from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.config import settings
from app.services.llm_service import LLMService

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    github_token: Optional[str] = None
    default_model: Optional[str] = None

@router.get("")
async def get_settings():
    active_key = settings.get_effective_api_key()
    masked_key = f"{active_key[:6]}...{active_key[-4:]}" if len(active_key) > 10 else ("Configured" if active_key else "Not configured")
    github_masked = f"{settings.GITHUB_TOKEN[:6]}...{settings.GITHUB_TOKEN[-4:]}" if settings.GITHUB_TOKEN else "Not configured"

    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "api_key_configured": bool(active_key),
        "api_key_masked": masked_key,
        "groq_api_key_configured": bool(settings.GROQ_API_KEY),
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY),
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "github_token_configured": bool(settings.GITHUB_TOKEN),
        "github_token_masked": github_masked,
        "default_model": settings.LLM_MODEL,
        "fast_model": settings.FAST_MODEL,
        "max_repo_size_mb": settings.MAX_REPO_SIZE_MB,
        "max_diff_lines": settings.MAX_DIFF_LINES,
        "available_providers": ["gemini", "groq", "openai", "custom"],
        "available_models": [
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
            "gpt-4o-mini",
            "gpt-4o"
        ]
    }

@router.post("/test-llm")
async def test_llm():
    service = LLMService()
    res = await service.test_connection()
    return res

@router.post("/update")
async def update_settings(req: SettingsUpdateRequest):
    if req.llm_provider:
        settings.LLM_PROVIDER = req.llm_provider
    if req.llm_api_key:
        settings.LLM_API_KEY = req.llm_api_key
    if req.llm_model:
        settings.LLM_MODEL = req.llm_model
    if req.default_model:
        settings.LLM_MODEL = req.default_model
    if req.groq_api_key:
        settings.GROQ_API_KEY = req.groq_api_key
    if req.gemini_api_key:
        settings.GEMINI_API_KEY = req.gemini_api_key
    if req.openai_api_key:
        settings.OPENAI_API_KEY = req.openai_api_key
    if req.github_token is not None:
        settings.GITHUB_TOKEN = req.github_token
    return {"status": "updated", "message": "Settings updated in current runtime session."}
