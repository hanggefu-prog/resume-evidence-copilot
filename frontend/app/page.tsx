"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, BriefcaseBusiness, FileText, Plus, Sparkles, Users } from "lucide-react";
import { PageHeading } from "@/components/page-heading";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type ObservabilityStats } from "@/lib/api";

export default function Home() {
  const [candidateCount, setCandidateCount] = useState<number | null>(null);
  const [jobCount, setJobCount] = useState<number | null>(null);
  const [stats, setStats] = useState<ObservabilityStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.candidates.list(), api.jobs.list(), api.observability.stats()])
      .then(([candidates, jobs, observability]) => {
        setCandidateCount(candidates.length);
        setJobCount(jobs.length);
        setStats(observability);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle>Can&apos;t reach the backend</CardTitle>
          <CardDescription>{error} — is it running at NEXT_PUBLIC_API_URL?</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="YOUR HIRING WORKSPACE" title="A clearer view of your next hire." description="Your candidates, opportunities, and AI insights. All in one place." action={<Link href="/candidates" className={buttonVariants()}><Plus size={16} /> Add candidate</Link>} />

      <section className="hero-panel" aria-labelledby="hero-title">
        <div>
          <span className="eyebrow">LESS SCREENING. MORE CONNECTING.</span>
          <h2 id="hero-title">Great teams start<br />with the right match.</h2>
          <p>Turn CVs and job descriptions into clear profiles, meaningful matches, and better interview conversations.</p>
          <div className="hero-actions">
            <Link href="/candidates" className={buttonVariants()}>Explore candidates <ArrowRight size={16} /></Link>
            <Link href="/jobs" className={buttonVariants({ variant: "outline" })}>View jobs</Link>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-art-center"><Sparkles size={34} /></div>
          <span className="hero-art-dot -top-2 left-7"><Users size={20} /></span>
          <span className="hero-art-dot right-0 top-20"><BriefcaseBusiness size={20} /></span>
          <span className="hero-art-dot bottom-0 left-3"><FileText size={20} /></span>
        </div>
      </section>

      <div className="grid gap-5 sm:grid-cols-3">
        <StatCard title="Candidates" value={candidateCount} href="/candidates" cta="View talent pool" icon={<Users size={20} />} />
        <StatCard title="Jobs" value={jobCount} href="/jobs" cta="Explore opportunities" icon={<BriefcaseBusiness size={20} />} tone="stat-icon-blue" />
        <StatCard title="LLM calls logged" value={stats?.total_calls ?? null} href="/observability" cta="View observability" icon={<Activity size={20} />} tone="stat-icon-amber" />
      </div>

      <Card>
        <CardHeader><CardTitle>From profile to possibility</CardTitle><CardDescription>A simple workflow for more informed hiring.</CardDescription></CardHeader>
        <CardContent className="workflow-grid">
          <div className="workflow-step"><span className="workflow-number">01 / BUILD YOUR POOL</span><h3>Bring your talent together</h3><p>Upload a CV or paste its text to extract skills, experience, and a structured candidate profile.</p></div>
          <div className="workflow-step"><span className="workflow-number">02 / FIND THE FIT</span><h3>Connect people with roles</h3><p>Add a job description and explore matches ranked by skills, experience, and semantic similarity.</p></div>
          <div className="workflow-step"><span className="workflow-number">03 / GO A LITTLE DEEPER</span><h3>Make the conversation count</h3><p>Review explained fit scores and generate interview questions tailored to each candidate and role.</p></div>
        </CardContent>
      </Card>

      {stats && stats.total_calls > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity size={17} className="text-primary" /> LLM observability summary</CardTitle><CardDescription>Visibility into the AI behind your workspace.</CardDescription></CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-3">
            <div><p className="text-xs text-muted-foreground">Success rate</p><p className="mt-2 text-2xl font-semibold tabular-nums">{((stats.success_rate ?? 0) * 100).toFixed(0)}<span className="ml-1 text-sm text-muted-foreground">%</span></p></div>
            <div><p className="text-xs text-muted-foreground">Average latency</p><p className="mt-2 text-2xl font-semibold tabular-nums">{stats.avg_latency_ms?.toFixed(0)}<span className="ml-1 text-sm text-muted-foreground">ms</span></p></div>
            <div><p className="text-xs text-muted-foreground">Total tokens</p><p className="mt-2 text-2xl font-semibold tabular-nums">{(stats.total_prompt_tokens + stats.total_completion_tokens).toLocaleString()}</p></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({ title, value, href, cta, icon, tone = "" }: {
  title: string; value: number | null; href: string; cta: string; icon: React.ReactNode; tone?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3"><CardDescription>{title}</CardDescription><span className={`stat-icon ${tone}`}>{icon}</span></div>
        <CardTitle className="stat-number">{value === null ? <Skeleton className="h-11 w-16" /> : value.toLocaleString()}</CardTitle>
      </CardHeader>
      <CardContent><Link href={href} className="stat-link">{cta}<ArrowRight size={15} aria-hidden="true" /></Link></CardContent>
    </Card>
  );
}
