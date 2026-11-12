from app.services.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.llm_client import LLMProvider, get_llm_provider


def get_llm() -> LLMProvider:
    return get_llm_provider()


def get_embedder() -> EmbeddingProvider:
    return get_embedding_provider()
