"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { api, ApiError, type RankedCandidateRead, type RequirementEvidence } from "@/lib/api";

const statusLabels = {
  supported: "有直接证据",
  needs_review: "待确认",
  not_mentioned: "简历未提及",
};

export function RequirementEvidenceDialog({ candidate, jobId }: { candidate: RankedCandidateRead; jobId: string }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<RequirementEvidence[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const highlight = useRef<HTMLElement>(null);
  const resume = candidate.raw_text;
  const quote = activeIndex === null ? null : rows?.[activeIndex]?.quote;
  const start = quote ? resume.indexOf(quote) : -1;

  useEffect(() => {
    if (activeIndex !== null) highlight.current?.focus();
  }, [activeIndex]);

  async function loadEvidence() {
    setOpen(true);
    if (rows || loading) return;
    setLoading(true);
    setError("");
    try {
      setRows(await api.scoring.evidence(candidate.id, jobId));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "暂时无法获取原文对照，请重试。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Button size="sm" onClick={loadEvidence}>原文对照</Button>
      <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) setActiveIndex(null); }}>
        <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>岗位要求与简历原文对照</DialogTitle>
            <DialogDescription>{candidate.parsed?.name || "候选人"} · 模型按岗位必备要求查找证据，点击引文可核对上下文。</DialogDescription>
          </DialogHeader>
          {loading && <p role="status">正在核对简历原文…</p>}
          {error && <div role="alert"><p>{error}</p><Button variant="outline" size="sm" onClick={loadEvidence}>重试</Button></div>}
          {rows?.length === 0 && <p>岗位尚未提取到必备技能或最低年限要求。</p>}
          <ul className="grid gap-3">
            {rows?.map((row, index) => (
              <li key={index} className="grid gap-2 rounded-lg border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium">{row.requirement}</span>
                  <Badge variant={row.status === "supported" ? "default" : "outline"}>{statusLabels[row.status]}</Badge>
                </div>
                {row.quote ? (
                  <button type="button" className="cursor-pointer border-l-2 border-primary pl-3 text-left text-sm whitespace-pre-wrap break-words hover:underline"
                    onClick={() => { setActiveIndex(index); if (activeIndex === index) highlight.current?.focus(); }}>
                    {row.quote}
                  </button>
                ) : row.status === "needs_review" && <p className="text-muted-foreground">没有可核验的引文，请人工确认。</p>}
              </li>
            ))}
          </ul>
          {quote && start >= 0 && (
            <section className="grid gap-2">
              <h3 className="font-medium">简历原文</h3>
              <div className="max-h-64 overflow-y-auto rounded-lg bg-muted p-3 whitespace-pre-wrap break-words">
                {resume.slice(0, start)}<mark ref={highlight} tabIndex={-1} className="rounded bg-amber-200 text-slate-950">{quote}</mark>{resume.slice(start + quote.length)}
              </div>
            </section>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
