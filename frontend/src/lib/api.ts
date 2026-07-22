/** 后端 API 封装。 */

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export interface AssetInfo {
  id: string;
  name: string;
  type: string;
  size: number;
}

export interface UploadResponse {
  job_id: string;
  assets: AssetInfo[];
  note: string;
  status: string;
}

export interface JobStatus {
  job_id: string;
  status: "uploaded" | "processing" | "done" | "failed";
  stage: string;
  progress: number;
  video_url: string | null;
  thumbnail_url: string | null;
  caption: string;
  hashtags: string[];
  template: string;
  note: string;
  assets_count: number;
  created_at: string | null;
  error: string | null;
}

export interface TemplateInfo {
  id: string;
  name: string;
  duration: number;
  hook_text: string;
  style_prompt: string;
}

function apiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${BASE}${path}`;
}

export function assetUrl(path: string | null): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${BASE}${path}`;
}

export async function uploadAssets(
  files: File[],
  note: string
): Promise<UploadResponse> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  form.append("note", note);

  const res = await fetch(apiUrl("/upload"), { method: "POST", body: form });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`上传失败 (${res.status}): ${t}`);
  }
  return res.json();
}

export async function generate(jobId: string, template?: string): Promise<void> {
  const res = await fetch(apiUrl(`/jobs/${jobId}/generate`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template: template || null }),
  });
  if (!res.ok && res.status !== 202) {
    const t = await res.text();
    throw new Error(`生成失败 (${res.status}): ${t}`);
  }
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(apiUrl(`/jobs/${jobId}`));
  if (!res.ok) throw new Error(`查询失败 (${res.status})`);
  return res.json();
}

export async function regenerate(jobId: string, template?: string): Promise<void> {
  const res = await fetch(apiUrl(`/jobs/${jobId}/regenerate`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template: template || null }),
  });
  if (!res.ok && res.status !== 202) {
    const t = await res.text();
    throw new Error(`重生失败 (${res.status}): ${t}`);
  }
}

export async function listTemplates(): Promise<TemplateInfo[]> {
  const res = await fetch(apiUrl("/templates"));
  if (!res.ok) return [];
  return res.json();
}
