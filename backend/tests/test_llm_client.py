"""Verifies the OpenRouter retry/backoff behavior discovered via a live smoke
test: free-tier models get upstream-rate-limited (429) intermittently. This
must be retried, not surfaced as a 500."""

import httpx
import pytest

from app.services.llm_client import LLMAuthenticationError, LLMProviderUnavailableError, OpenRouterProvider


def _fake_response(status_code: int, json_body: dict, retry_after: str = "0") -> httpx.Response:
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return httpx.Response(
        status_code=status_code,
        json=json_body,
        headers={"Retry-After": retry_after},
        request=request,
    )


def test_retries_on_429_then_succeeds(monkeypatch):
    responses = [
        _fake_response(429, {"error": "rate limited"}),
        _fake_response(
            200,
            {"choices": [{"message": {"content": "hello"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}},
        ),
    ]

    def fake_post(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = OpenRouterProvider(api_key="test-key", model="test-model")
    result = provider.complete("system", "user")

    assert result.content == "hello"
    assert responses == []  # both queued responses were consumed


def test_raises_unavailable_after_max_retries(monkeypatch):
    def fake_post(*args, **kwargs):
        return _fake_response(429, {"error": "rate limited"})

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = OpenRouterProvider(api_key="test-key", model="test-model")
    with pytest.raises(LLMProviderUnavailableError):
        provider.complete("system", "user")


def test_non_retryable_error_raises_immediately(monkeypatch):
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(1)
        return _fake_response(401, {"error": "bad key"})

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = OpenRouterProvider(api_key="test-key", model="test-model")
    with pytest.raises(LLMAuthenticationError, match="401"):
        provider.complete("system", "user")

    assert len(calls) == 1  # no retry for a non-transient error
