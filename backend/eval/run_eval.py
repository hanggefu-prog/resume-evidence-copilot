"""Offline eval harness for the parse -> score pipeline.

Uses the REAL LLM provider (OpenRouter) — this hits the network and is
subject to free-tier rate limits, so it's a manual dev tool, not part of the
automated pytest suite. Run: python -m eval.run_eval
"""

from __future__ import annotations

from eval.dataset import EVAL_CASES

from app.services.cv_parser import parse_cv
from app.services.jd_parser import parse_jd
from app.services.llm_client import get_llm_provider
from app.services.scorer import score_fit

TIER_BOUNDS = {"strong": (70, 100), "moderate": (40, 69.999), "weak": (0, 39.999)}


def tier_for_score(score: float) -> str:
    for tier, (lo, hi) in TIER_BOUNDS.items():
        if lo <= score <= hi:
            return tier
    return "unknown"


def run() -> None:
    llm = get_llm_provider()
    correct = 0

    for case in EVAL_CASES:
        candidate = parse_cv(llm, case["candidate_text"]).value
        job = parse_jd(llm, case["job_text"]).value
        fit = score_fit(llm, candidate, job).value

        actual_tier = tier_for_score(fit.score)
        is_correct = actual_tier == case["expected_tier"]
        correct += int(is_correct)

        status = "OK  " if is_correct else "MISS"
        print(f"[{status}] {case['name']}: score={fit.score} expected={case['expected_tier']} actual={actual_tier}")
        print(f"        reasoning: {fit.reasoning}")

    total = len(EVAL_CASES)
    print(f"\n{correct}/{total} correct ({correct / total:.0%})")


if __name__ == "__main__":
    run()
