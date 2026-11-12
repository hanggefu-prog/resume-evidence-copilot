"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { PageHeading } from "@/components/page-heading";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type ObservabilityStats } from "@/lib/api";

export default function ObservabilityPage() {
  const [stats, setStats] = useState<ObservabilityStats | null>(null);

  useEffect(() => {
    api.observability.stats().then(setStats).catch(() => {});
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="BEHIND THE INTELLIGENCE" title="Observability" description="A clear picture of AI activity, reliability, and usage across your workspace." />

      {!stats && <Skeleton className="h-40 w-full" />}

      {stats && stats.total_calls === 0 && (
        <Card>
          <CardContent className="text-muted-foreground py-8 text-center">
            <div className="empty-state"><span className="upload-icon"><Activity size={22} aria-hidden="true" /></span><strong>Your AI activity will appear here</strong><p>Parse a candidate or job to start tracking calls, tokens, and response times.</p></div>
          </CardContent>
        </Card>
      )}

      {stats && stats.total_calls > 0 && (
        <>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total calls" value={stats.total_calls} />
            <MetricCard label="Success rate" value={`${((stats.success_rate ?? 0) * 100).toFixed(0)}%`} />
            <MetricCard label="Avg latency" value={`${stats.avg_latency_ms?.toFixed(0)}ms`} />
            <MetricCard label="Avg attempts" value={stats.avg_attempts?.toFixed(2) ?? "—"} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Token usage</CardTitle>
              <CardDescription>Prompt and completion tokens used across recorded AI calls.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <p className="text-muted-foreground text-sm">Prompt tokens</p>
                <p className="text-2xl font-semibold">{stats.total_prompt_tokens.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-sm">Completion tokens</p>
                <p className="text-2xl font-semibold">{stats.total_completion_tokens.toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Calls by purpose</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {Object.entries(stats.by_purpose).map(([purpose, count]) => (
                <div key={purpose} className="border-b py-4 last:border-0">
                  <div className="flex items-center justify-between gap-4"><span className="break-all text-sm">{purpose}</span><span className="text-muted-foreground text-sm tabular-nums">{count}</span></div>
                  <div className="purpose-track" aria-hidden="true"><div className="purpose-fill" style={{ width: `${Math.min(100, count / stats.total_calls * 100)}%` }} /></div>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}
