import json
import uuid

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "",
        "skills": ["Python", "FastAPI"],
        "years_experience": 4,
        "education": [],
        "summary": "Backend engineer.",
    }
)


def test_create_candidate(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)

    response = client.post("/candidates", json={"raw_text": "Jane Doe, backend engineer"})

    assert response.status_code == 201
    body = response.json()
    assert body["parsed"]["name"] == "Jane Doe"
    assert "Python" in body["parsed"]["skills"]
    assert uuid.UUID(body["id"])  # valid UUID


def test_create_candidate_rejects_malformed_llm_output(client, mock_llm):
    mock_llm.responses.extend(["garbage", "garbage", "garbage"])

    response = client.post("/candidates", json={"raw_text": "some cv"})

    assert response.status_code == 422


def test_create_candidate_rejects_empty_text(client, mock_llm):
    response = client.post("/candidates", json={"raw_text": ""})
    assert response.status_code == 422


def test_list_candidates(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    client.post("/candidates", json={"raw_text": "Jane Doe"})

    response = client.get("/candidates")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_candidate_by_id(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    created = client.post("/candidates", json={"raw_text": "Jane Doe"}).json()

    response = client.get(f"/candidates/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_candidate_not_found(client, mock_llm):
    response = client.get(f"/candidates/{uuid.uuid4()}")
    assert response.status_code == 404


def test_upload_candidate_txt_file(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)

    response = client.post(
        "/candidates/upload",
        files={"file": ("cv.txt", b"Jane Doe, backend engineer", "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["parsed"]["name"] == "Jane Doe"


def test_upload_candidate_rejects_unsupported_extension(client, mock_llm):
    response = client.post(
        "/candidates/upload",
        files={"file": ("cv.docx", b"binary garbage", "application/octet-stream")},
    )

    assert response.status_code == 422
