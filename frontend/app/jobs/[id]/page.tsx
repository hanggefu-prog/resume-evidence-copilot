"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeading } from "@/components/page-heading";
import { RequirementEvidenceDialog } from "@/components/requirement-evidence";
import { InterviewPrepPanel } from "@/components/interview-prep-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError, type JobRead, type RankedCandidateRead, type ScoreRead } from "@/lib/api";

type DialogState =
  | { type: "score"; candidateName: string; data: ScoreRead | null; error: string | null }
  | { type: "questions"; candidateName: string; data: string[] | null; error: string | null }
  | null;

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<JobRead | null>(null);
  const [candidates, setCandidates] = useState<RankedCandidateRead[] | null>(null);
  const [dialog, setDialog] = useState<DialogState>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    api.jobs.get(id).then(setJob).catch(() => {});
    api.search.candidatesForJob(id).then(setCandidates).catch(() => setCandidates([]));
  }, [id]);

  async function runScore(candidate: RankedCandidateRead) {
    setPendingId(candidate.id);
    setDialog({ type: "score", candidateName: candidate.parsed?.name ?? "Candidate", data: null, error: null });
    try {
      const score = await api.scoring.create(candidate.id, id);
      setDialog({ type: "score", candidateName: candidate.parsed?.name ?? "Candidate", data: score, error: null });
    } catch (err) {
      setDialog({
        type: "score",
        candidateName: candidate.parsed?.name ?? "Candidate",
        data: null,
        error: err instanceof ApiError ? err.detail : "Scoring failed",
      });
    } finally {
      setPendingId(null);
    }
  }

  async function runQuestions(candidate: RankedCandidateRead) {
    setPendingId(candidate.id);
    setDialog({ type: "questions", candidateName: candidate.parsed?.name ?? "Candidate", data: null, error: null });
    try {
      const result = await api.interviews.generateQuestions(candidate.id, id);
      setDialog({
        type: "questions",
        candidateName: candidate.parsed?.name ?? "Candidate",
        data: result.questions,
        error: null,
      });
    } catch (err) {
      setDialog({
        type: "questions",
        candidateName: candidate.parsed?.name ?? "Candidate",
        data: null,
        error: err instanceof ApiError ? err.detail : "Question generation failed",
      });
    } finally {
      setPendingId(null);
    }
  }

  if (!job) return <Skeleton className="h-40 w-full" />;
  const parsed = job.parsed;

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="ROLE OVERVIEW" title={parsed?.title || "Job"} description={parsed?.company} />

      <Card>
        <CardHeader>
          <CardTitle>Requirements</CardTitle>
          <CardDescription>Minimum {parsed?.min_years_experience} years experience</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-1">
            {parsed?.required_skills.map((s) => (
              <Badge key={s}>{s}</Badge>
            ))}
            {parsed?.nice_to_have_skills.map((s) => (
              <Badge key={s} variant="outline">
                {s}
              </Badge>
            ))}
          </div>
          {parsed?.summary && <p className="text-sm">{parsed.summary}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ranked candidates</CardTitle>
          <CardDescription>
            Explore candidate matches. Scores and interview questions may take 20–30 seconds to generate.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {candidates === null && <Skeleton className="h-16 w-full" />}
          {candidates?.length === 0 && (
            <p className="text-muted-foreground text-sm">No candidates uploaded yet.</p>
          )}
          {candidates?.map((c) => (
            <div key={c.id} className="match-row flex flex-col items-stretch justify-between gap-4 sm:flex-row sm:items-center">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">{c.parsed?.name}</p>
                  <Badge variant="outline">rerank {c.rerank_score.toFixed(2)}</Badge>
                </div>
                <p className="text-muted-foreground truncate text-sm">
                  {c.parsed?.skills.join(", ")}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <RequirementEvidenceDialog key={id} candidate={c} jobId={id} />
                <InterviewPrepPanel key={`prep-${id}`} candidateId={c.id} name={c.parsed?.name ?? "候选人"} jobId={id} />
                <Button size="sm" variant="secondary" disabled={pendingId === c.id} onClick={() => runScore(c)}>
                  {pendingId === c.id ? "…" : "Score"}
                </Button>
                <Button size="sm" variant="outline" disabled={pendingId === c.id} onClick={() => runQuestions(c)}>
                  {pendingId === c.id ? "…" : "Interview Qs"}
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Dialog open={dialog !== null} onOpenChange={(open) => !open && setDialog(null)}>
        <DialogContent>
          {dialog?.type === "score" && (
            <>
              <DialogHeader>
                <DialogTitle>Fit score — {dialog.candidateName}</DialogTitle>
                <DialogDescription>Transparent LLM-generated reasoning, not a black box.</DialogDescription>
              </DialogHeader>
              {dialog.error && <p className="text-destructive text-sm">{dialog.error}</p>}
              {!dialog.error && !dialog.data && <Skeleton className="h-24 w-full" />}
              {dialog.data && (
                <div className="flex flex-col gap-3">
                  <p className="rounded-xl border border-primary/15 bg-secondary px-5 py-6 text-4xl font-semibold text-primary">{dialog.data.score}<span className="ml-1 text-base font-normal text-muted-foreground">/100</span></p>
                  <p className="text-sm">{dialog.data.reasoning}</p>
                  <div className="flex flex-wrap gap-1">
                    {dialog.data.matched_skills?.map((s) => (
                      <Badge key={s}>{s}</Badge>
                    ))}
                    {dialog.data.missing_skills?.map((s) => (
                      <Badge key={s} variant="destructive">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          {dialog?.type === "questions" && (
            <>
              <DialogHeader>
                <DialogTitle>Interview questions — {dialog.candidateName}</DialogTitle>
                <DialogDescription>Targeted at this candidate&apos;s specific gaps vs. the role.</DialogDescription>
              </DialogHeader>
              {dialog.error && <p className="text-destructive text-sm">{dialog.error}</p>}
              {!dialog.error && !dialog.data && <Skeleton className="h-24 w-full" />}
              {dialog.data && (
                <ol className="flex list-decimal flex-col gap-4 pl-5 text-sm leading-7 marker:font-semibold marker:text-primary">
                  {dialog.data.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ol>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
