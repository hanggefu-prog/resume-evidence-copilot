# Demo script

Two things to produce, both from the same walkthrough: four screenshots for the README, and a
~2-3 minute Loom recording. Do the screenshots first (also serves as your dry run for the video).

## Setup

```bash
./scripts/setup-env.sh
docker compose up -d postgres backend frontend
docker compose run --rm backend python -m seed.seed_data   # only if the demo DB is empty
```

Open http://localhost:3000.

## Screenshots (save to `docs/screenshots/`)

1. **`dashboard.png`** — the home page (`/`). Shows candidate/job counts and the observability
   summary card. Wait for it to finish loading real numbers before capturing.
2. **`job-detail.png`** — click into any job with a good spread of candidates (e.g. "Backend
   Engineer at Acme AI" if it's still seeded). Capture the ranked-candidates list with the
   rerank scores visible.
3. **`score-dialog.png`** — on that same job page, click "Score" on the top-ranked candidate.
   Wait ~20-30s for the real LLM call (free-tier latency — this is expected). Capture the dialog
   once the score + reasoning renders.
4. **`interview-questions.png`** — click "Interview Qs" on the same candidate. Wait for the
   response, capture the 5 questions.

## Loom recording — talking points

Keep it tight, narrate over the same click path:

1. **Open on the dashboard.** *"This is a full-stack AI recruitment tool — FastAPI backend,
   Next.js frontend, real RAG search against a Postgres/pgvector store, all running against a
   free-tier LLM to keep it a $0-cost demo."*
2. **Upload a CV** (paste text or a real file) live. *"CVs and job descriptions get parsed into
   structured JSON by an LLM — schema-validated, with an automatic repair-retry loop, since
   free-tier models aren't as reliable at strict JSON as GPT-4 or Claude."*
3. **Go to a job, show the ranked candidates.** *"This is RAG in practice: pgvector does the
   semantic retrieval, then a re-ranking layer corrects for skill overlap and experience — not
   just 'reads similar,' but 'actually qualifies.'"*
4. **Click Score.** While it's loading: *"Free-tier models mean occasional 20-30 second waits and
   occasional rate-limiting — both handled explicitly with retry/backoff, not glossed over."*
   Then show the result: *"Transparent reasoning, not a black-box number."*
5. **Click Interview Qs.** *"Targeted at this candidate's specific gaps against this specific
   role, not generic questions."*
6. **Open `/observability`.** *"Every LLM call is logged — tokens, latency, success rate. This is
   the cost/observability layer real production AI systems need, and it's the same layer that'd
   catch a cost blowup if this moved to a paid model."*
7. **Close on the repo.** *"58 tests, CI on GitHub Actions, fully Dockerized, architecture and
   cost/safety tradeoffs written up in the README — link in the description."*

Upload to Loom, add the link to the README's Status section once done.
