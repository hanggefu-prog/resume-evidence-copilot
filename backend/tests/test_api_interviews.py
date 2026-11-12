import json
import uuid

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe", "email": "", "phone": "", "skills": ["Python"],
        "years_experience": 5, "education": [], "summary": "",
    }
)
VALID_JD_JSON = json.dumps(
    {
        "title": "Backend Engineer", "company": "Acme", "required_skills": ["Python"],
        "nice_to_have_skills": [], "min_years_experience": 3, "summary": "",
    }
)
VALID_QUESTIONS_JSON = json.dumps({"questions": ["Q1", "Q2", "Q3", "Q4", "Q5"]})


def test_create_interview_questions(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    candidate = client.post("/candidates", json={"raw_text": "Jane Doe"}).json()
    mock_llm.responses.append(VALID_JD_JSON)
    job = client.post("/jobs", json={"raw_text": "Backend Engineer at Acme"}).json()

    mock_llm.responses.append(VALID_QUESTIONS_JSON)
    response = client.post(f"/interviews/{candidate['id']}/{job['id']}/questions")

    assert response.status_code == 200
    assert len(response.json()["questions"]) == 5


def test_interview_questions_candidate_not_found(client, mock_llm):
    response = client.post(f"/interviews/{uuid.uuid4()}/{uuid.uuid4()}/questions")
    assert response.status_code == 404
