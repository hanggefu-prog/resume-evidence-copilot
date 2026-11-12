"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type CandidateRead, type RankedJobRead } from "@/lib/api";

export default function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<CandidateRead | null>(null);
  const [matches, setMatches] = useState<RankedJobRead[] | null>(null);

  useEffect(() => {
    api.candidates.get(id).then(setCandidate).catch(() => {});
    api.search.jobsForCandidate(id).then(setMatches).catch(() => setMatches([]));
  }, [id]);

  if (!candidate) return <Skeleton className="h-40 w-full" />;
  const parsed = candidate.parsed;

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="CANDIDATE PROFILE" title={parsed?.name || "Candidate"} description={<>{parsed?.email} {parsed?.phone && `· ${parsed.phone}`}</>} />

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>{parsed?.years_experience} years experience</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-1">
            {parsed?.skills.map((s) => (
              <Badge key={s} variant="secondary">
                {s}
              </Badge>
            ))}
          </div>
          {parsed?.summary && <p className="text-sm">{parsed.summary}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Matching jobs</CardTitle>
          <CardDescription>Ranked by vector similarity, skill overlap, and experience fit</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {matches === null && <Skeleton className="h-16 w-full" />}
          {matches?.length === 0 && <p className="text-muted-foreground text-sm">No jobs posted yet.</p>}
          {matches?.map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="match-row flex flex-wrap items-center justify-between gap-3"
            >
              <div>
                <p className="font-medium">{job.parsed?.title}</p>
                <p className="text-muted-foreground text-sm">{job.parsed?.company}</p>
              </div>
              <Badge variant="outline">rerank {job.rerank_score.toFixed(2)}</Badge>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
