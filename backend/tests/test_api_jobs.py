import json
import uuid

VALID_JD_JSON = json.dumps(
    {
        "title": "Full-Stack AI Engineer",
        "company": "Acme AI",
        "required_skills": ["Python", "React"],
        "nice_to_have_skills": [],
        "min_years_experience": 3,
        "summary": "Build production AI features.",
    }
)


def test_create_job(client, mock_llm):
    mock_llm.responses.append(VALID_JD_JSON)

    response = client.post("/jobs", json={"raw_text": "Full-Stack AI Engineer at Acme AI"})

    assert response.status_code == 201
    body = response.json()
    assert body["parsed"]["title"] == "Full-Stack AI Engineer"
    assert uuid.UUID(body["id"])


def test_create_job_rejects_malformed_llm_output(client, mock_llm):
    mock_llm.responses.extend(["nope", "nope", "nope"])

    response = client.post("/jobs", json={"raw_text": "some jd"})

    assert response.status_code == 422


def test_list_jobs(client, mock_llm):
    mock_llm.responses.append(VALID_JD_JSON)
    client.post("/jobs", json={"raw_text": "Full-Stack AI Engineer at Acme AI"})

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_job_not_found(client, mock_llm):
    response = client.get(f"/jobs/{uuid.uuid4()}")
    assert response.status_code == 404


def test_upload_job_txt_file(client, mock_llm):
    mock_llm.responses.append(VALID_JD_JSON)

    response = client.post(
        "/jobs/upload",
        files={"file": ("jd.txt", b"Full-Stack AI Engineer at Acme AI", "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["parsed"]["title"] == "Full-Stack AI Engineer"
