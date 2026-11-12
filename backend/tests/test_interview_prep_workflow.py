from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.workflows.interview_prep import build_graph


def test_manual_only_resume_from_checkpoint():
    saver = InMemorySaver()
    config = {"configurable": {"thread_id": "manual-only"}}

    def unexpected(*_):
        raise AssertionError("Unexpected model call after resume")

    first = build_graph(saver, list, unexpected)
    assert first.invoke({}, config)["__interrupt__"]
    restored = build_graph(saver, unexpected, unexpected)
    state = restored.invoke(
        Command(resume={"reviews": {}, "manual_questions": [" 原样保留？ "]}), config
    )
    assert state["outline"] == [
        {
            "text": " 原样保留？ ",
            "source": "manual",
            "requirement_id": None,
            "reason": None,
        }
    ]
