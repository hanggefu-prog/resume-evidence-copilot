import json

from app.services.interview_guide import generate_guide
from app.services.llm_client import MockLLMProvider


def test_only_outline_evidence_is_sent_and_groups_are_aligned():
    follow = [{"condition": "描述团队成果", "question": "你做了什么？"},
              {"condition": "提到指标", "question": "如何测量？"}]
    groups = [{"outline_index": i, "main_question": "请介绍具体经历。", "follow_ups": follow}
              for i in [1, 0]]
    llm = MockLLMProvider([json.dumps({"groups": groups})])
    manual = "  最满意的决定？ "
    result = generate_guide(llm, [
        {"source": "manual", "text": manual},
        {"source": "generated", "text": "优化经历？", "requirement_id": 1},
    ], [{"quote": "SKIPPED"}, {"quote": "查询优化"}], {"reviews": {"1": {"note": "复盘"}}})
    assert [g.outline_index for g in result.value.groups] == [0, 1]
    assert result.value.groups[0].main_question == manual
    assert "SKIPPED" not in llm.calls[0][1]
    assert json.loads(llm.calls[0][1])[1]["focus"] == "复盘"
