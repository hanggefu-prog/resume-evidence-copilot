const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface CandidateParsed {
  name: string;
  email: string;
  phone: string;
  skills: string[];
  years_experience: number;
  education: string[];
  summary: string;
}

export interface CandidateRead {
  id: string;
  raw_text: string;
  parsed: CandidateParsed | null;
  created_at: string;
}

export interface JobParsed {
  title: string;
  company: string;
  required_skills: string[];
  nice_to_have_skills: string[];
  min_years_experience: number;
  summary: string;
}

export interface JobRead {
  id: string;
  raw_text: string;
  parsed: JobParsed | null;
  created_at: string;
}

export interface RankedCandidateRead extends CandidateRead {
  vector_similarity: number;
  skill_overlap: number;
  experience_fit: number;
  rerank_score: number;
}

export interface RankedJobRead extends JobRead {
  vector_similarity: number;
  skill_overlap: number;
  experience_fit: number;
  rerank_score: number;
}

export interface ScoreRead {
  id: string;
  candidate_id: string;
  job_id: string;
  score: number;
  reasoning: string;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  created_at: string;
}

export interface InterviewQuestionsRead {
  questions: string[];
}

export interface RequirementEvidence {
  requirement: string;
  status: "supported" | "needs_review" | "not_mentioned";
  quote: string | null;
}

export interface PrepReview {
  decision: "pending" | "ask" | "skip";
  note: string;
}

export interface PrepEdits {
  reviews: Record<string, PrepReview>;
  manual_questions: string[];
}

export interface InterviewPrep {
  question_guide: {
    outline_index: number;
    main_question: string;
    follow_ups: { condition: string; question: string }[];
  }[] | null;
  id: string;
  version: number;
  evidence: RequirementEvidence[];
  edits: PrepEdits;
  outline: {
    text: string;
    source: "generated" | "manual";
    requirement_id: number | null;
    reason: string | null;
  }[] | null;
}

export interface ObservabilityStats {
  total_calls: number;
  success_rate: number | null;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  avg_latency_ms: number | null;
  avg_attempts: number | null;
  by_purpose: Record<string, number>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export const api = {
  prep: {
    questionGuide: (id: string) =>
      request<InterviewPrep>(`/interview-prep/${id}/question-guide`, { method: "POST" }),
    open: (candidate: string, job: string) =>
      request<InterviewPrep>(`/interview-prep/open/${candidate}/${job}`, { method: "POST" }),
    save: (id: string, version: number, edits: PrepEdits) =>
      request<InterviewPrep>(`/interview-prep/${id}`, {
        method: "PUT", body: JSON.stringify({ version, edits }),
      }),
    generate: (id: string, version: number) =>
      request<InterviewPrep>(`/interview-prep/${id}/generate`, {
        method: "POST", body: JSON.stringify({ version }),
      }),
  },
  candidates: {
    list: () => request<CandidateRead[]>("/candidates"),
    get: (id: string) => request<CandidateRead>(`/candidates/${id}`),
    create: (rawText: string) =>
      request<CandidateRead>("/candidates", {
        method: "POST",
        body: JSON.stringify({ raw_text: rawText }),
      }),
    upload: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API_URL}/candidates/upload`, { method: "POST", body: form });
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new ApiError(response.status, body.detail ?? response.statusText);
      }
      return response.json() as Promise<CandidateRead>;
    },
  },
  jobs: {
    list: () => request<JobRead[]>("/jobs"),
    get: (id: string) => request<JobRead>(`/jobs/${id}`),
    create: (rawText: string) =>
      request<JobRead>("/jobs", { method: "POST", body: JSON.stringify({ raw_text: rawText }) }),
    upload: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API_URL}/jobs/upload`, { method: "POST", body: form });
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new ApiError(response.status, body.detail ?? response.statusText);
      }
      return response.json() as Promise<JobRead>;
    },
  },
  search: {
    candidatesForJob: (jobId: string, topN = 10) =>
      request<RankedCandidateRead[]>(`/search/jobs/${jobId}/candidates?top_n=${topN}`),
    jobsForCandidate: (candidateId: string, topN = 10) =>
      request<RankedJobRead[]>(`/search/candidates/${candidateId}/jobs?top_n=${topN}`),
  },
  scoring: {
    evidence: (candidateId: string, jobId: string) =>
      request<RequirementEvidence[]>(`/scoring/${candidateId}/${jobId}/evidence`, { method: "POST" }),
    create: (candidateId: string, jobId: string) =>
      request<ScoreRead>(`/scoring/${candidateId}/${jobId}`, { method: "POST" }),
    list: (candidateId: string, jobId: string) =>
      request<ScoreRead[]>(`/scoring/${candidateId}/${jobId}`),
  },
  interviews: {
    generateQuestions: (candidateId: string, jobId: string) =>
      request<InterviewQuestionsRead>(`/interviews/${candidateId}/${jobId}/questions`, {
        method: "POST",
      }),
  },
  observability: {
    stats: () => request<ObservabilityStats>("/observability/stats"),
  },
};
