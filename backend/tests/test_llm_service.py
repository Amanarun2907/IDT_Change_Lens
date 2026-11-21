import pytest
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.security.secret_redaction import redact_secrets

class SampleSchema(BaseModel):
    summary: str
    score: int

def test_secret_redaction():
    text = "API_KEY = 'gsk_1234567890123456789012345678901234567890' and GHP = 'ghp_123456789012345678901234567890123456'"
    redacted = redact_secrets(text)
    assert "gsk_" not in redacted
    assert "ghp_" not in redacted
    assert "[REDACTED" in redacted

def test_llm_service_provider_resolution():
    service_gemini = LLMService(provider="gemini", api_key="AIzaSyTest")
    assert service_gemini.provider == "gemini"
    assert "generativelanguage" in service_gemini.base_url

    service_groq = LLMService(provider="groq", api_key="gsk_Test")
    assert service_groq.provider == "groq"
    assert "groq.com" in service_groq.base_url

def test_json_cleaner():
    service = LLMService()
    raw_markdown = "Here is the response:\n```json\n{\"summary\": \"Test summary\", \"score\": 42}\n```\nHope it helps!"
    cleaned = service._clean_json_text(raw_markdown)
    assert cleaned == '{"summary": "Test summary", "score": 42}'

@pytest.mark.asyncio
async def test_mock_handler():
    def mock_gen(system, user, schema):
        return SampleSchema(summary="Mocked result", score=99)

    LLMService.set_mock_handler(mock_gen)
    try:
        service = LLMService()
        res = await service.generate_json("system", "user", SampleSchema)
        assert res.summary == "Mocked result"
        assert res.score == 99
    finally:
        LLMService.set_mock_handler(None)
