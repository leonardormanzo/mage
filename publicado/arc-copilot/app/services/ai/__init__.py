from app.core.config import get_settings
from app.services.ai.providers import (
    EmbeddingProvider,
    GeminiProvider,
    LLMProvider,
    MockEmbeddingProvider,
    MockLLMProvider,
    MockTranscriptionProvider,
    MockVisionProvider,
    TranscriptionProvider,
    VisionProvider,
)


def get_embedding_provider() -> EmbeddingProvider:
    """Gemini quando há chave configurada; vetor local por hashing no modo demonstração."""
    settings = get_settings()
    if settings.ai_mode:
        return GeminiProvider(api_key=settings.gemini_api_key)
    return MockEmbeddingProvider()


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.ai_mode:
        return GeminiProvider(api_key=settings.gemini_api_key)
    return MockLLMProvider()


__all__ = [
    "EmbeddingProvider",
    "GeminiProvider",
    "LLMProvider",
    "MockEmbeddingProvider",
    "MockLLMProvider",
    "MockTranscriptionProvider",
    "MockVisionProvider",
    "TranscriptionProvider",
    "VisionProvider",
    "get_embedding_provider",
    "get_llm_provider",
]
