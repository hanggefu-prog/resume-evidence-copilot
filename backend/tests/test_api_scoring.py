import json
import uuid

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe", "email": "", "phone": "", "skills": ["Python", "FastAPI"],
        "years_experience": 5, "education": [], "summary": "Backend engineer.",
    }
)
VALID_JD_JSON = json.dumps(
    {
        "title": "Backend Engineer", "company": "Acme", "required_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": [], "min_years_experience": 3, "summary": "Backend role.",
    }
)
VALID_SCORE_JSON = json.dumps(
    {"score": 90, "reasoning": "Great match.", "matched_skills": ["Python", "FastAPI"], "missing_skills": []}
)


def _create_candidate_and_job(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    candidate = client.post("/candidates", json={"raw_text": "Jane Doe"}).json()
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()
    return candidate, job


def test_create_score(client, mock_llm):
    candidate, job = _create_candidate_and_job(client, mock_llm)
    mock_llm.responses.append(VALID_SCORE_JSON)

    response = client.post(f"/scoring/{candidate['id']}/{job['id']}")

    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 90
    assert "Python" in body["matched_skills"]


def test_score_candidate_not_found(client, mock_llm):
    response = client.post(f"/scoring/{uuid.uuid4()}/{uuid.uuid4()}")
    assert response.status_code == 404


def test_score_job_not_found(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    candidate = client.post("/candidates", json={"raw_text": "Jane Doe"}).json()

    response = client.post(f"/scoring/{candidate['id']}/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_scores(client, mock_llm):
    candidate, job = _create_candidate_and_job(client, mock_llm)
    mock_llm.responses.append(VALID_SCORE_JSON)
    client.post(f"/scoring/{candidate['id']}/{job['id']}")

    response = client.get(f"/scoring/{candidate['id']}/{job['id']}")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_evidence_checks_quotes_and_preserves_requirement_order(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    resume = "在订单服务中使用 Python。"
    candidate = client.post("/candidates", json={"raw_text": resume}).json()
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()
    mock_llm.responses.append(json.dumps({"findings": [
        {"requirement_id": 2, "status": "not_mentioned", "quote": ""},
        {"requirement_id": 1, "status": "supported", "quote": "使用 FastAPI 开发。"},
        {"requirement_id": 0, "status": "supported", "quote": resume},
    ]}))

    response = client.post(f"/scoring/{candidate['id']}/{job['id']}/evidence")

    assert response.status_code == 200
    assert response.json() == [
        {"requirement": "Python", "status": "supported", "quote": resume},
        {"requirement": "FastAPI", "status": "needs_review", "quote": None},
        {"requirement": "至少 3 年工作经验", "status": "not_mentioned", "quote": None},
    ]
