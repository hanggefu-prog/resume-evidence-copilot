"""Seed the database with fake candidates and jobs for local dev/demo.

Builds parsed JSON directly (no LLM call) for speed and determinism — this is
seed data, not a parsing test. Run with: python -m seed.seed_data
"""

from __future__ import annotations

import random

from faker import Faker

from app.db import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.embeddings import get_embedding_provider

fake = Faker()

SKILL_POOL = [
    "Python", "TypeScript", "React", "Next.js", "FastAPI", "PostgreSQL",
    "Docker", "AWS", "LangGraph", "SQLAlchemy", "Node.js", "GraphQL",
    "Kubernetes", "Redis", "Supabase", "Pydantic", "pytest", "CI/CD",
]

JOB_TITLES = [
    "Full-Stack AI Engineer", "Applied AI Engineer", "Backend Engineer",
    "AI Product Engineer", "Voice AI Engineer", "Senior Python Engineer",
]


def build_candidate() -> Candidate:
    skills = random.sample(SKILL_POOL, k=random.randint(3, 7))
    years = round(random.uniform(0.5, 12), 1)
    name = fake.name()
    parsed = {
        "name": name,
        "email": fake.email(),
        "phone": fake.phone_number(),
        "skills": skills,
        "years_experience": years,
        "education": [f"{fake.random_element(['BSc','MSc','BA'])} {fake.job()}"],
        "summary": f"{name} has {years} years of experience across {', '.join(skills[:3])}.",
    }
    raw_text = (
        f"{name}\n{parsed['email']} | {parsed['phone']}\n\n"
        f"Skills: {', '.join(skills)}\n"
        f"Experience: {years} years\n\n{parsed['summary']}"
    )
    embedder = get_embedding_provider()
    return Candidate(raw_text=raw_text, parsed=parsed, embedding=embedder.embed(raw_text))


def build_job() -> Job:
    title = random.choice(JOB_TITLES)
    company = fake.company()
    required = random.sample(SKILL_POOL, k=random.randint(3, 6))
    nice_to_have = random.sample([s for s in SKILL_POOL if s not in required], k=2)
    min_years = random.choice([1, 2, 3, 5])
    parsed = {
        "title": title,
        "company": company,
        "required_skills": required,
        "nice_to_have_skills": nice_to_have,
        "min_years_experience": min_years,
        "summary": f"{company} is hiring a {title} with {min_years}+ years experience.",
    }
    raw_text = (
        f"{title} at {company}\n\n"
        f"Required: {', '.join(required)}\n"
        f"Nice to have: {', '.join(nice_to_have)}\n"
        f"Minimum experience: {min_years} years\n\n{parsed['summary']}"
    )
    embedder = get_embedding_provider()
    return Job(raw_text=raw_text, parsed=parsed, embedding=embedder.embed(raw_text))


def run(num_candidates: int = 15, num_jobs: int = 8) -> None:
    db = SessionLocal()
    try:
        for _ in range(num_candidates):
            db.add(build_candidate())
        for _ in range(num_jobs):
            db.add(build_job())
        db.commit()
        print(f"Seeded {num_candidates} candidates and {num_jobs} jobs.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
