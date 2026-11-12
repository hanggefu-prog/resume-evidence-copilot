# Cost & safety notes

Honest accounting of what this costs to run, what could go wrong, and what's deliberately
simplified. Written to be read by a hiring manager, not just a checklist.

## Cost

- **LLM calls**: OpenRouter free-tier models (`:free` suffix) — $0 per call, rate-limited by the
  underlying provider rather than billed. `GET /observability/stats` tracks token usage per call
  type so the moment this swaps to a paid model, real cost is visible immediately rather than
  discovered on a bill. Average observed latency on the current default model
  (`openai/gpt-oss-20b:free`) is ~20-30s/call — free-tier tradeoff, not a bug.
- **Embeddings**: local `sentence-transformers` (`all-MiniLM-L6-v2`), not an API. Zero per-call
  cost, no external dependency for the single most call-heavy operation (every candidate/job
  gets embedded on upload).
- **Database**: single shared Supabase project across this and other portfolio apps, isolated by
  Postgres schema per app. This is a deliberate cost/quota tradeoff (Supabase free tier caps
  active projects) — in a real multi-tenant product this would be a bigger isolation boundary
  (separate database or project per tenant), and that's flagged here rather than glossed over.

## Reliability

- **Malformed LLM output**: schema-validated with a repair-retry loop (up to 3 attempts, the
  validation error is fed back to the model). See `docs/architecture.md`.
- **Upstream rate-limiting**: transport-level retry with backoff on 429/502/503/504, honoring
  `Retry-After`. After 3 attempts, surfaces as a `503` to the caller — an explicit "try again"
  signal, not a silent failure or a crash.
- **Test isolation**: tests run against a dedicated `recruitment_copilot_test` database, never
  the dev/demo one. (This was a real bug caught during development — see git history — where
  running `pytest` was silently wiping seeded demo data.)

## Known simplifications (stated proactively, not hidden)

- **Re-ranking is a heuristic, not a cross-encoder model.** Vector similarity + skill overlap +
  minimum experience fit, weighted 50/30/20. A cross-encoder is the standard upgrade path; skipped
  here because there's no labeled relevance data yet to prove it would outperform the heuristic,
  and it adds a real inference-cost/latency dependency for an unproven gain.
- **Experience fit uses total years.** Candidates earn proportional credit up to the job's
  minimum and full credit thereafter. A job with no minimum gives all candidates full credit.
- **Eval harness is a sanity check, not a benchmark.** 12 hand-labeled candidate/job pairs
  (`backend/eval/dataset.py`). This catches obviously-broken scoring; it is not statistically
  large enough to claim a validated accuracy number, and isn't presented as one.

## Safety

- **Prompt injection surface**: CVs and job descriptions are attacker-controllable free text fed
  directly into an LLM prompt. Current mitigation is limited to strict schema validation on the
  *output* (a malicious CV can't make the parser return arbitrary unstructured content — it still
  has to fit `CandidateParsed`). There is no input-side sanitization or instruction-boundary
  hardening yet; for a real production deployment accepting public CV uploads, that's the next
  thing to build, not an afterthought.
- **File upload limits**: 5MB cap, extension allowlist (`.pdf`, `.txt`, `.md`) enforced in
  `file_extraction.py` — rejects anything else with a clear 422, not a silent failure.
- **No auth yet**: this is a portfolio demo, not a deployed multi-user product. Every endpoint is
  open. Adding auth (Supabase auth, given the stack) is the first thing that would need to happen
  before this touched real candidate data.
