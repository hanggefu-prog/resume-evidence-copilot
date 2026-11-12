"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Upload, Sparkles, Users } from "lucide-react";
import { PageHeading } from "@/components/page-heading";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { api, ApiError, type CandidateRead } from "@/lib/api";

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateRead[]>([]);
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.candidates.list().then(setCandidates).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  async function submitText() {
    if (!rawText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.candidates.create(rawText);
      setRawText("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to parse candidate");
    } finally {
      setLoading(false);
    }
  }

  async function submitFile(file: File) {
    setLoading(true);
    setError(null);
    try {
      await api.candidates.upload(file);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to parse candidate");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeading eyebrow="YOUR TALENT POOL" title="Candidates" description="Great people, ready to be discovered. Build and explore your candidate profiles." action={<span className="flex items-center gap-2 rounded-full border bg-white px-4 py-2 text-xs text-muted-foreground"><Users size={15} />{candidates.length} candidates</span>} />

      <Card className="upload-card">
        <CardHeader>
          <div className="upload-heading"><span className="upload-icon"><FileText size={21} aria-hidden="true" /></span><div><CardTitle>Add a candidate</CardTitle><CardDescription>Paste a CV below, or upload a PDF, TXT, or Markdown file.</CardDescription></div></div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Textarea
            aria-label="Candidates source text"
            placeholder="Paste CV text here…"
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
          <CardTitle>Candidate directory</CardTitle>
          <CardDescription>{candidates.length} candidate(s) · Select a profile to explore matches</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Skills</TableHead>
                <TableHead>Years</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {candidates.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium"><span className="person-avatar" aria-hidden="true">{c.parsed?.name?.charAt(0).toUpperCase() || "?"}</span>{c.parsed?.name || "—"}</TableCell>
                  <TableCell className="max-w-md">
                    <div className="flex flex-wrap gap-1">
                      {c.parsed?.skills.slice(0, 6).map((s) => (
                        <Badge key={s} variant="secondary">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>{c.parsed?.years_experience ?? "—"}</TableCell>
                  <TableCell>
                    <Link href={`/candidates/${c.id}`} className="text-primary text-sm hover:underline">
                      View →
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {candidates.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground text-center">
                    <div className="empty-state"><span className="upload-icon"><Users size={22} aria-hidden="true" /></span><strong>No candidates yet</strong><p>Your talent pool starts with one person. Add a CV above to get started.</p></div>
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
