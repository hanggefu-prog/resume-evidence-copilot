import json
import uuid

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe", "email": "", "phone": "", "skills": ["Python", "FastAPI"],
        "years_experience": 5, "education": [], "summary": "",
    }
)
VALID_JD_JSON = json.dumps(
    {
        "title": "Backend Engineer", "company": "Acme", "required_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": [], "min_years_experience": 3, "summary": "",
    }
)


def test_search_candidates_for_job(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    candidate = client.post("/candidates", json={"raw_text": "Jane Doe backend engineer"}).json()
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()

    response = client.get(f"/search/jobs/{job['id']}/candidates")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == candidate["id"]
    assert "rerank_score" in body[0]


def test_search_jobs_for_candidate(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    candidate = client.post("/candidates", json={"raw_text": "Jane Doe backend engineer"}).json()
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()

    response = client.get(f"/search/candidates/{candidate['id']}/jobs")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == job["id"]


def test_search_job_not_found(client, mock_llm):
    response = client.get(f"/search/jobs/{uuid.uuid4()}/candidates")
    assert response.status_code == 404


def test_search_respects_top_n(client, mock_llm):
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()
    for i in range(3):
        mock_llm.responses.append(VALID_CV_JSON)
        client.post("/candidates", json={"raw_text": f"Candidate {i}"})

    response = client.get(f"/search/jobs/{job['id']}/candidates?top_n=2")

    assert response.status_code == 200
    assert len(response.json()) == 2
