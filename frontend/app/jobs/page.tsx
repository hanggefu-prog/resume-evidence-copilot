"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Upload, Sparkles, BriefcaseBusiness } from "lucide-react";
import { PageHeading } from "@/components/page-heading";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { api, ApiError, type JobRead } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobRead[]>([]);
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.jobs.list().then(setJobs).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  async function submitText() {
    if (!rawText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.jobs.create(rawText);
      setRawText("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to parse job");
    } finally {
      setLoading(false);
    }
  }

  async function submitFile(file: File) {
    setLoading(true);
    setError(null);
    try {
      await api.jobs.upload(file);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to parse job");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="YOUR OPPORTUNITIES" title="Jobs" description="Define the role. Discover the people who could make it their own." action={<span className="flex items-center gap-2 rounded-full border bg-white px-4 py-2 text-xs text-muted-foreground"><BriefcaseBusiness size={15} />{jobs.length} jobs</span>} />

      <Card className="upload-card">
        <CardHeader>
          <div className="upload-heading"><span className="upload-icon"><FileText size={21} aria-hidden="true" /></span><div><CardTitle>Add a job</CardTitle><CardDescription>Paste a job description below, or upload a PDF, TXT, or Markdown file.</CardDescription></div></div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Textarea
            aria-label="Jobs source text"
            placeholder="Paste job description here…"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={5}
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={submitText} disabled={loading || !rawText.trim()}>
              <Sparkles size={15} aria-hidden="true" /> {loading ? "Parsing…" : "Parse text"}
            </Button>
            <span className="text-muted-foreground text-sm">or</span>
            <label className={buttonVariants({ variant: "outline" })}>
              <input
                type="file"
                accept=".pdf,.txt,.md"
                className="sr-only"
                onChange={(e) => e.target.files?.[0] && submitFile(e.target.files[0])}
              />
              <Upload size={15} aria-hidden="true" /> Upload file
            </label>
          </div>
          {error && <p className="text-destructive text-sm">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Job directory</CardTitle>
          <CardDescription>{jobs.length} job(s) · Select a profile to explore matches</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Required skills</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((j) => (
                <TableRow key={j.id}>
                  <TableCell className="font-medium">{j.parsed?.title || "—"}</TableCell>
                  <TableCell>{j.parsed?.company || "—"}</TableCell>
                  <TableCell className="max-w-md">
                    <div className="flex flex-wrap gap-1">
                      {j.parsed?.required_skills.slice(0, 6).map((s) => (
                        <Badge key={s} variant="secondary">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Link href={`/jobs/${j.id}`} className="text-primary text-sm hover:underline">
                      View →
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {jobs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground text-center">
                    <div className="empty-state"><span className="upload-icon"><BriefcaseBusiness size={22} aria-hidden="true" /></span><strong>No jobs yet</strong><p>Your next great hire starts here. Add a job description above to get started.</p></div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
