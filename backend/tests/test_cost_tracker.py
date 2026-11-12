from app.services.cost_tracker import get_observability_stats, record_llm_call
from app.services.llm_client import LLMUsage


def test_stats_empty_when_no_calls(db_session):
    stats = get_observability_stats(db_session)
    assert stats["total_calls"] == 0
    assert stats["success_rate"] is None


def test_stats_aggregate_across_calls(db_session):
    record_llm_call(
        db_session, purpose="candidate.parse", provider="mock", model="mock-model",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=5), attempts=1,
        latency_ms=100.0, success=True,
    )
    record_llm_call(
        db_session, purpose="candidate.parse", provider="mock", model="mock-model",
        usage=LLMUsage(prompt_tokens=20, completion_tokens=10), attempts=2,
        latency_ms=200.0, success=False, error="boom",
    )
    db_session.commit()

    stats = get_observability_stats(db_session)

    assert stats["total_calls"] == 2
    assert stats["success_rate"] == 0.5
    assert stats["total_prompt_tokens"] == 30
    assert stats["total_completion_tokens"] == 15
    assert stats["avg_latency_ms"] == 150.0
    assert stats["avg_attempts"] == 1.5
    assert stats["by_purpose"] == {"candidate.parse": 2}
