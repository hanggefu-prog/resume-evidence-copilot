import json

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe", "email": "", "phone": "", "skills": ["Python"],
        "years_experience": 5, "education": [], "summary": "",
    }
)


def test_observability_stats_empty(client, mock_llm):
    response = client.get("/observability/stats")
    assert response.status_code == 200
    assert response.json()["total_calls"] == 0


def test_observability_stats_after_a_call(client, mock_llm):
    mock_llm.responses.append(VALID_CV_JSON)
    client.post("/candidates", json={"raw_text": "Jane Doe"})

    response = client.get("/observability/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_calls"] == 1
    assert body["success_rate"] == 1.0
    assert body["by_purpose"] == {"candidate.parse": 1}
