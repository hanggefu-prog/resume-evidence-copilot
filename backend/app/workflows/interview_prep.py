from typing import TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy.engine import make_url

from app.config import settings
from app.schemas.interview_prep import Question


class PrepState(TypedDict, total=False):
    evidence: list[dict]
    selected: list[dict]
    manual_questions: list[str]
    generated: list[dict]
    outline: list[dict]


def build_graph(saver, collect_evidence, generate_questions):
    def collect(state):
        return {"evidence": collect_evidence()}

    def review(state):
        edits = interrupt("review")
        selected = []
        for index, row in enumerate(state["evidence"]):
            choice = edits["reviews"].get(str(index), {})
            if choice.get("decision") == "ask":
                selected.append(
                    {**row, "requirement_id": index, "note": choice["note"]}
                )
        return {"selected": selected, "manual_questions": edits["manual_questions"]}

    def generate(state):
        return {"generated": generate_questions(state["selected"])}

    def assemble(state):
        outline = [
            Question(source="generated", **q) for q in state.get("generated", [])
        ]
        outline.extend(
            Question(source="manual", text=q) for q in state["manual_questions"]
        )
        return {"outline": [q.model_dump() for q in outline]}

    graph = StateGraph(PrepState)
    graph.add_node("collect", collect)
    graph.add_node("review", review)
    graph.add_node("generate", generate)
    graph.add_node("assemble", assemble)
    graph.add_edge(START, "collect")
    graph.add_edge("collect", "review")
    graph.add_conditional_edges(
        "review",
        lambda s: "generate" if s["selected"] else "assemble",
        ["generate", "assemble"],
    )
    graph.add_edge("generate", "assemble")
    graph.add_edge("assemble", END)
    return graph.compile(checkpointer=saver)


def setup_checkpoints():
    url = make_url(settings.database_url).set(drivername="postgresql")
    with PostgresSaver.from_conn_string(
        url.render_as_string(hide_password=False)
    ) as saver:
        saver.setup()


if __name__ == "__main__":
    setup_checkpoints()
