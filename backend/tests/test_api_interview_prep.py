import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db import SessionLocal
from app.models import Candidate, Job
from app.workflows.interview_prep import setup_checkpoints


@pytest.fixture(scope="module", autouse=True)
def checkpoints():
    setup_checkpoints()


def prepare(client, mock_llm, skills):
    with SessionLocal.begin() as db:
        candidate = Candidate(raw_text="Used SQL", parsed={})
        job = Job(
            raw_text="Engineer",
            parsed={
                "title": "Engineer",
                "company": "",
                "required_skills": skills,
                "nice_to_have_skills": [],
                "min_years_experience": 0,
                "summary": "",
            },
        )
        db.add_all([candidate, job])
        db.flush()
        url = f"/interview-prep/open/{candidate.id}/{job.id}"
    if skills:
        findings = [
            {"requirement_id": i, "status": "not_mentioned", "quote": ""}
            for i in range(len(skills))
        ]
        findings[0].update(status="supported", quote="Used SQL")
        mock_llm.responses.append(json.dumps({"findings": findings}))
    response = client.post(url)
    assert response.status_code == 200, response.text
    return url, response.json()


def test_review_save_resume_and_retry(client, mock_llm):
    url, draft = prepare(client, mock_llm, ["SQL", "Python", "R"])
    path = "/interview-prep/" + draft["id"]
    edits = draft["edits"]
    assert set(edits["reviews"]) == {"1", "2"}
    assert client.post(path + "/generate", json={"version": 1}).status_code == 422
    edits["reviews"]["1"] = {"decision": "ask", "note": "关注个人贡献"}
    edits["reviews"]["2"]["decision"] = "skip"
    edits["manual_questions"] = [" 手写问题？ "]
    body = {"version": 1, "edits": edits}
    assert client.put(path, json=body).status_code == 200
    assert client.put(path, json=body).status_code == 409
    assert client.post(url).json()["edits"] == edits

    # Wrong IDs must not attach a question to a skipped or supported requirement.
    mock_llm.responses.extend(['{"questions": []}'] * 3)
    assert client.post(path + "/generate", json={"version": 2}).status_code == 422
    mock_llm.responses.append(
        json.dumps(
            {
                "questions": [
                    {
                        "requirement_id": 1,
                        "text": "具体负责什么？",
                        "reason": "核实经验",
                    }
                ]
            }
        )
    )
    result = client.post(path + "/generate", json={"version": 2})
    assert result.status_code == 200, result.text
    outline = result.json()["outline"]
    assert [q["requirement_id"] for q in outline] == [1, None]
    assert outline[1]["text"] == edits["manual_questions"][0]
    assert client.post(path + "/generate", json={"version": 2}).json() == result.json()
    assert client.post(url).json() == result.json()


def test_empty_outline_without_model_call(client, mock_llm):
    _, draft = prepare(client, mock_llm, [])
    response = client.post(
        f"/interview-prep/{draft['id']}/generate", json={"version": 1}
    )
    assert response.status_code == 200, response.text
    assert response.json()["outline"] == []


def test_optional_followup_on_supported_quote(client, mock_llm):
    url, draft = prepare(client, mock_llm, ["SQL"])
    path = "/interview-prep/" + draft["id"]
    edits = draft["edits"]
    assert edits["reviews"] == {}
    edits["reviews"]["0"] = {"decision": "ask", "note": "个人贡献"}
    saved = client.put(path, json={"version": draft["version"], "edits": edits})
    assert saved.status_code == 200
    assert client.post(url).json()["edits"] == edits
    mock_llm.responses.append(json.dumps({"questions": [
        {"requirement_id": 0, "text": "你负责哪部分 SQL 工作？", "reason": "了解个人贡献"}
    ]}))
    result = client.post(path + "/generate", json={"version": saved.json()["version"]})
    assert result.status_code == 200
    assert result.json()["outline"][0]["requirement_id"] == 0
    item, = json.loads(mock_llm.calls[-1][1])
    assert (item["status"], item["quote"], item["note"]) == ("supported", "Used SQL", "个人贡献")


def test_simultaneous_generation_uses_model_once(client, mock_llm):
    _, draft = prepare(client, mock_llm, ["SQL", "Python"])
    path = "/interview-prep/" + draft["id"]
    edits = draft["edits"]
    edits["reviews"]["1"]["decision"] = "ask"
    assert client.put(path, json={"version": 1, "edits": edits}).status_code == 200
    mock_llm.responses.append(
        json.dumps(
            {
                "questions": [
                    {"requirement_id": 1, "text": "请举例说明。", "reason": "核实经验"}
                ]
            }
        )
    )

    def generate():
        return client.post(path + "/generate", json={"version": 2})

    with ThreadPoolExecutor(2) as pool:
        responses = [pool.submit(generate) for _ in range(2)]
        first, second = [future.result() for future in responses]
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(mock_llm.calls) == 2  # one evidence check and one generation
