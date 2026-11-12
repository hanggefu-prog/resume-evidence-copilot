"""Small hand-labeled eval set: candidate/job text pairs with an expected fit
tier. Not statistically significant (12 cases) — this is a regression check
against obviously-wrong scoring, not a validated benchmark. Expand before
citing it as evidence of anything beyond "the pipeline isn't badly broken"."""

EVAL_CASES = [
    {
        "name": "strong-backend-match",
        "candidate_text": (
            "Maria Nowak. 6 years experience. Skills: Python, FastAPI, PostgreSQL, "
            "Docker, AWS, SQLAlchemy. Built and deployed production REST APIs."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker. "
            "Minimum 4 years experience."
        ),
        "expected_tier": "strong",
    },
    {
        "name": "strong-fullstack-ai-match",
        "candidate_text": (
            "Tom Becker. 5 years experience. Skills: Python, FastAPI, React, TypeScript, "
            "LLM APIs, embeddings, PostgreSQL. Shipped a RAG-based support tool."
        ),
        "job_text": (
            "Full-Stack AI Engineer at Acme AI. Required: Python, FastAPI, React, "
            "TypeScript, LLM/RAG experience. Minimum 3 years."
        ),
        "expected_tier": "strong",
    },
    {
        "name": "moderate-partial-skill-overlap",
        "candidate_text": (
            "Ana Silva. 3 years experience. Skills: Python, Django, MySQL, basic Docker."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker, "
            "AWS. Minimum 3 years experience."
        ),
        "expected_tier": "moderate",
    },
    {
        "name": "moderate-junior-for-mid-role",
        "candidate_text": (
            "Chris Lee. 1.5 years experience. Skills: Python, FastAPI, PostgreSQL."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker. "
            "Minimum 4 years experience."
        ),
        "expected_tier": "moderate",
    },
    {
        "name": "weak-domain-mismatch-frontend-only",
        "candidate_text": (
            "Sam Park. 4 years experience. Skills: HTML, CSS, Figma, WordPress, no backend experience."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker, AWS. "
            "Minimum 4 years experience."
        ),
        "expected_tier": "weak",
    },
    {
        "name": "weak-completely-unrelated-field",
        "candidate_text": (
            "Jordan Kim. 5 years experience as a graphic designer. Skills: Photoshop, "
            "Illustrator, branding, print design."
        ),
        "job_text": (
            "Full-Stack AI Engineer at Acme AI. Required: Python, FastAPI, React, "
            "TypeScript, LLM/RAG experience. Minimum 3 years."
        ),
        "expected_tier": "weak",
    },
    {
        "name": "strong-voice-ai-match",
        "candidate_text": (
            "Nina Petrov. 4 years experience. Skills: Python, FastAPI, WebSockets, "
            "Whisper, speech-to-text, text-to-speech, real-time systems."
        ),
        "job_text": (
            "Voice AI Engineer at VoiceCo. Required: Python, WebSockets, speech "
            "processing (STT/TTS). Minimum 2 years."
        ),
        "expected_tier": "strong",
    },
    {
        "name": "moderate-overqualified-but-missing-key-skill",
        "candidate_text": (
            "David Chen. 8 years experience. Skills: Java, Spring Boot, Oracle DB, "
            "microservices architecture."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker. "
            "Minimum 3 years experience."
        ),
        "expected_tier": "moderate",
    },
    {
        "name": "weak-no-experience-listed",
        "candidate_text": "Alex Rivera. Recent graduate, no professional experience listed. Skills: basic Python.",
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL, Docker, AWS. "
            "Minimum 4 years experience."
        ),
        "expected_tier": "weak",
    },
    {
        "name": "strong-exact-stack-match",
        "candidate_text": (
            "Lucia Rossi. 3 years experience. Skills: Python, React, TypeScript, "
            "Tailwind, LangGraph, Supabase."
        ),
        "job_text": (
            "Full-Stack AI Engineer at Acme AI. Required: Python, React, TypeScript, "
            "LangGraph, Supabase. Minimum 3 years."
        ),
        "expected_tier": "strong",
    },
    {
        "name": "moderate-adjacent-stack",
        "candidate_text": (
            "Omar Haddad. 4 years experience. Skills: Node.js, Express, MongoDB, React."
        ),
        "job_text": (
            "Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL. "
            "Minimum 3 years experience."
        ),
        "expected_tier": "moderate",
    },
    {
        "name": "weak-wrong-seniority-direction",
        "candidate_text": (
            "Priya Nair. 12 years experience as an engineering director. Skills: "
            "team leadership, budget planning, stakeholder management."
        ),
        "job_text": (
            "Junior Backend Engineer at DataCo. Required: Python, FastAPI, PostgreSQL. "
            "Minimum 0-1 years experience, entry level."
        ),
        "expected_tier": "weak",
    },
]
