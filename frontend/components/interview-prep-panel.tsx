"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError, type InterviewPrep, type PrepEdits, type PrepReview } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const labels = { supported: "已有原文支持", needs_review: "证据待核实", not_mentioned: "简历未提及" };
const field = "w-full rounded-md border bg-background p-2";
const message = (error: unknown) => error instanceof Error ? error.message : "请求失败，请重试";

export function InterviewPrepPanel({candidateId, jobId, name}: {candidateId: string; jobId: string; name: string}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<InterviewPrep | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const saved = useRef<InterviewPrep | null>(null);
  const latest = useRef<PrepEdits | null>(null);
  const queue = useRef<Promise<boolean> | null>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const scrollKey = `prep-position:${candidateId}:${jobId}`;

  useEffect(() => {
    function warn(event: BeforeUnloadEvent) {
      if (saved.current && saved.current.edits !== latest.current) event.preventDefault();
    }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);

  async function load() {
    setOpen(true);
    setBusy(true);
    setError("");
    try {
      const data = await api.prep.open(candidateId, jobId);
      saved.current = data;
      latest.current = data.edits;
      setDraft(data);
      setConflict(false);
      requestAnimationFrame(() => {
        if (scroll.current) scroll.current.scrollTop = Number(sessionStorage.getItem(scrollKey) ?? 0);
      });
    } catch (err) { setError(message(err)); }
    finally { setBusy(false); }
  }

  // Keep at most one request in flight. Edits made meanwhile are saved against
  // the acknowledged version, without replacing newer text in the editor.
  function flush(): Promise<boolean> {
    if (queue.current) return queue.current;
    if (!saved.current || saved.current.edits === latest.current) return Promise.resolve(true);
    setSaving(true);
    queue.current = (async () => {
      try {
        while (saved.current && latest.current && saved.current.edits !== latest.current) {
          const edits = latest.current;
          const data = await api.prep.save(saved.current.id, saved.current.version, edits);
          saved.current = { ...data, edits };
        }
        setError("");
        return true;
      } catch (err) {
        setError(message(err));
        setConflict(err instanceof ApiError && err.status === 409);
        return false;
      } finally {
        setSaving(false);
        queue.current = null;
      }
    })();
    return queue.current;
  }

  function edit(edits: PrepEdits) {
    if (!draft) return;
    latest.current = edits;
    setDraft({ ...draft, edits });
    void flush();
  }

  function review(index: number, change: Partial<PrepReview>) {
    if (!draft) return;
    const { reviews } = draft.edits;
    const previous = reviews[index] ?? { decision: "skip", note: "" };
    edit({ ...draft.edits, reviews: { ...reviews, [index]: { ...previous, ...change } } });
  }

  async function generate() {
    if (!await flush() || !saved.current) return;
    setBusy(true);
    setError("");
    try {
      const data = await api.prep.generate(saved.current.id, saved.current.version);
      saved.current = data;
      latest.current = data.edits;
      setDraft(data);
      if (scroll.current) scroll.current.scrollTop = 0;
    } catch (err) {
      setError(message(err));
      setConflict(err instanceof ApiError && err.status === 409);
    } finally { setBusy(false); }
  }

  const supported = draft?.evidence.flatMap((row, index) => row.status === "supported" ? [{row, index}] : []) ?? [];
  const pending = Object.values(draft?.edits.reviews ?? {}).filter(row => row.decision === "pending").length;
  return <>
    <Button size="sm" variant="outline" onClick={load}>根据简历证据准备面试</Button>
    <Dialog open={open} onOpenChange={async next => {
      if (!next && !busy && (conflict || await flush())) setOpen(false);
    }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{draft?.outline ? "面试提纲" : "根据简历证据准备面试"}</DialogTitle>
          <DialogDescription>{name}</DialogDescription>
        </DialogHeader>
        {error && <p role="alert" className="text-destructive">{error}</p>}
        {conflict && <Button variant="outline" onClick={load}>载入最新草稿</Button>}
        {!draft && !busy && <Button onClick={load}>重新打开</Button>}
        {busy && <p role="status">{draft ? "正在处理…" : "正在读取草稿或核对简历证据…"}</p>}
        {draft && <div ref={scroll} className="max-h-[65dvh] space-y-4 overflow-y-auto pr-2"
          onScroll={event => sessionStorage.setItem(scrollKey, String(event.currentTarget.scrollTop))}>
          {supported.length > 0 && <details className="rounded-md border p-3">
            <summary>已有原文支持（{supported.length}）{draft.outline === null && " · 可选追问"}</summary>
            {supported.map(({row, index}) => {
              const choice = draft.edits.reviews[index];
              return <section key={index} className="mt-3 space-y-2 border-t pt-3">
                <strong>{row.requirement}</strong>
                <blockquote className="border-l-2 pl-3">{row.quote}</blockquote>
                {draft.outline === null && <fieldset disabled={busy || conflict} className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={choice?.decision === "ask"}
                      onChange={e => review(index, {decision: e.target.checked ? "ask" : "skip"})}/>
                    加入追问
                  </label>
                  {choice?.decision === "ask" && <label className="block">追问方向（选填）
                    <textarea className={field} value={choice.note} onChange={e => review(index, {note: e.target.value})}/>
                  </label>}
                </fieldset>}
              </section>;
            })}
          </details>}
          {draft.outline !== null ? <>
            {draft.outline.length === 0 && <p>本次没有待核实的问题。</p>}
            <ol className="list-decimal space-y-4 pl-5">{draft.outline.map((q,i) => {
              const row = q.requirement_id === null ? null : draft.evidence[q.requirement_id];
              return <li key={i}><strong className="whitespace-pre-wrap">{q.text}</strong>
                {row ? <div className="mt-1 space-y-1 text-muted-foreground">
                  <p>{row.requirement} · {labels[row.status]}</p>
                  {row.quote && <blockquote>{row.quote}</blockquote>}<p>提问理由：{q.reason}</p>
                </div> : <p className="text-muted-foreground">手动添加</p>}
              </li>;
            })}</ol>
          </> : <fieldset disabled={busy || conflict} className="space-y-4">
            {draft.evidence.map((row, index) => {
              const choice = draft.edits.reviews[index];
              if (row.status === "supported" || !choice) return null;
              return <section key={index} className="space-y-2 rounded-lg border p-3">
                <h3 className="font-semibold">{row.requirement}</h3>
                <p className="text-muted-foreground">{labels[row.status]}</p>
                {row.quote && <blockquote className="border-l-2 pl-3">{row.quote}</blockquote>}
                <div className="flex gap-2">{(["ask", "skip"] as const).map(value =>
                  <Button key={value} size="sm" variant={choice.decision === value ? "default" : "outline"}
                    aria-pressed={choice.decision === value} onClick={() => review(index, {decision: value})}>
                    {value === "ask" ? "追问" : "跳过"}
                  </Button>)}</div>
                {choice.decision === "ask" && <label className="block">追问方向（选填）
                  <textarea className={field} value={choice.note} onChange={e => review(index, {note:e.target.value})}/>
                </label>}
              </section>;
            })}
            <h3 className="font-semibold">手动添加的问题</h3>
            {draft.edits.manual_questions.map((q,i) => <div key={i} className="flex items-center gap-2">
              <textarea className={field} aria-label={`手写问题 ${i+1}`} value={q} onChange={e =>
                edit({...draft.edits, manual_questions: draft.edits.manual_questions.map((v,j) => j === i ? e.target.value : v)})}/>
              <Button size="sm" variant="ghost" onClick={() =>
                edit({...draft.edits, manual_questions: draft.edits.manual_questions.filter((_,j) => j !== i)})}>移除</Button>
            </div>)}
            <Button variant="outline" onClick={() => edit({...draft.edits, manual_questions:[...draft.edits.manual_questions,""]})}>添加问题</Button>
          </fieldset>}
        </div>}
        {draft && draft.outline === null && <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3">
          <span role="status" className="text-muted-foreground">{saving ? "正在保存…" : error ? "" : "草稿已保存"}{pending > 0 && ` · ${pending} 项待决定`}</span>
          {error && !conflict && <Button variant="outline" onClick={() => void flush()}>重试保存</Button>}
          <Button disabled={busy || saving || conflict || pending > 0 || draft.edits.manual_questions.some(q => !q.trim())}
            onClick={generate}>生成面试提纲</Button>
        </div>}
      </DialogContent>
    </Dialog>
  </>;
}
