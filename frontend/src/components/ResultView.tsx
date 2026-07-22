"use client";

import { useState } from "react";
import { JobStatus, assetUrl, regenerate, listTemplates, TemplateInfo } from "@/lib/api";

interface ResultViewProps {
  job: JobStatus;
  onRegenerating: () => void;
  onReset: () => void;
}

export default function ResultView({ job, onRegenerating, onReset }: ResultViewProps) {
  const [copied, setCopied] = useState(false);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [showTpl, setShowTpl] = useState(false);
  const [regenLoading, setRegenLoading] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);

  const captionFull = `${job.caption}\n\n${job.hashtags.join(" ")}`;

  async function copyCaption() {
    try {
      await navigator.clipboard.writeText(captionFull);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  async function doRegenerate(template?: string) {
    setRegenLoading(true);
    setShowTpl(false);
    try {
      await regenerate(job.job_id, template);
      onRegenerating();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setRegenLoading(false);
    }
  }

  async function openTemplates() {
    if (templates.length === 0) {
      const t = await listTemplates();
      setTemplates(t);
    }
    setShowTpl((s) => !s);
  }

  return (
    <div className="space-y-5">
      {/* 视频预览 */}
      <div className="overflow-hidden rounded-3xl bg-black shadow-lg">
        <video
          key={job.video_url}
          src={assetUrl(job.video_url)}
          poster={assetUrl(job.thumbnail_url) || undefined}
          controls
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          onError={() => setVideoError("视频加载失败，请刷新页面重试")}
          className="mx-auto aspect-[9/16] max-h-[70vh] w-full object-contain"
        />
        {videoError && (
          <p className="bg-black py-2 text-center text-xs text-red-400">{videoError}</p>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="grid grid-cols-2 gap-3">
        <a
          href={assetUrl(job.video_url) || "#"}
          download={`${job.job_id}.mp4`}
          className="btn-ghost flex items-center justify-center gap-1.5"
        >
          📥 下载视频
        </a>
        <button onClick={copyCaption} className="btn-ghost flex items-center justify-center gap-1.5">
          {copied ? "✅ 已复制" : "📋 复制文案"}
        </button>
      </div>

      {/* 换风格重生 */}
      <button
        onClick={openTemplates}
        disabled={regenLoading}
        className="btn-ghost w-full"
      >
        {regenLoading ? "重新生成中…" : "🔄 换个风格重新生成"}
      </button>

      {showTpl && (
        <div className="grid grid-cols-2 gap-2">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => doRegenerate(t.id)}
              className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-left text-xs"
            >
              <p className="font-semibold text-gray-800">{t.name}</p>
              <p className="text-gray-400">{t.duration}s · {t.hook_text}</p>
            </button>
          ))}
          <button
            onClick={() => doRegenerate(undefined)}
            className="col-span-2 rounded-xl border border-brand-200 bg-brand-50 px-3 py-2.5 text-center text-xs font-semibold text-brand-600"
          >
            🎲 随机风格
          </button>
        </div>
      )}

      {/* 文案卡片 */}
      <div className="card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-800">📝 IG Caption</h3>
          <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-600">
            {job.template}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
          {job.caption}
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.hashtags.map((h) => (
            <span key={h} className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-brand-600">
              {h}
            </span>
          ))}
        </div>
      </div>

      <button onClick={onReset} className="w-full py-2 text-center text-sm text-gray-400">
        生成新视频 →
      </button>
    </div>
  );
}
