import type { InterviewPrep } from "@/lib/api";

export function InterviewQuestionGuide({ prep }: { prep: InterviewPrep }) {
  return <ol className="space-y-4">
    {prep.question_guide?.map(group => {
      const item = prep.outline?.[group.outline_index];
      const evidence = item?.requirement_id != null ? prep.evidence[item.requirement_id] : null;
      return <li key={group.outline_index} className="space-y-3 rounded-lg border p-4">
        <p className="text-muted-foreground">{evidence?.requirement ?? "手写题"}</p>
        <h3 className="whitespace-pre-wrap font-semibold">{group.main_question}</h3>
        {group.follow_ups.map((follow, index) => <div key={index} className="border-l-2 pl-3">
          <p className="text-muted-foreground">{follow.condition}</p>
          <p>{follow.question}</p>
        </div>)}
        {evidence?.quote && <details><summary>查看简历原文</summary>
          <blockquote className="mt-2 whitespace-pre-wrap">{evidence.quote}</blockquote>
        </details>}
      </li>;
    })}
  </ol>;
}
