"use client";

import { useEffect, useRef, useState } from "react";
import Uploader from "@/components/Uploader";
import ProgressView from "@/components/ProgressView";
import ResultView from "@/components/ResultView";
import {
  uploadAssets,
  generate,
  getJob,
  JobStatus,
  assetUrl,
  apiUrl,
} from "@/lib/api";

type Phase = "upload" | "processing" | "done" | "failed";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [brandLogo, setBrandLogo] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    // 拉取品牌配置，若已配置 Logo 则在顶栏展示（Phase 2.1）
    fetch(apiUrl("/brand"))
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d?.logo_url && setBrandLogo(d.logo_url))
      .catch(() => {});
  }, []);

  function startPolling(id: string) {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(async () => {
      try {
        const st = await getJob(id);
        setJob(st);
        if (st.status === "done") {
          if (timerRef.current) clearInterval(timerRef.current);
          setPhase("done");
        } else if (st.status === "failed") {
          if (timerRef.current) clearInterval(timerRef.current);
          setError(st.error || "生成失败");
          setPhase("failed");
        }
      } catch (e) {
        /* 忽略瞬时错误继续轮询 */
      }
    }, 1500);
  }

  async function handleGenerate(files: File[], note: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await uploadAssets(files, note);
      setJobId(res.job_id);
      await generate(res.job_id);
      setPhase("processing");
      startPolling(res.job_id);
    } catch (e) {
      setError((e as Error).message);
      setPhase("failed");
    } finally {
      setLoading(false);
    }
  }

  function handleRegenerating() {
    setPhase("processing");
    if (jobId) startPolling(jobId);
  }

  function handleReset() {
    if (timerRef.current) clearInterval(timerRef.current);
    setPhase("upload");
    setJob(null);
    setJobId(null);
    setError(null);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col px-4 pb-10">
      {/* 顶栏 */}
      <header className="flex items-center justify-between py-5">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-gray-900">
            MakanReel
          </h1>
          <p className="text-xs text-gray-400">Singapore F&B · AI 短视频生成 · Phase 1 + 2.1</p>
        </div>
        {brandLogo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={assetUrl(brandLogo)}
            alt="Brand"
            className="h-8 w-auto rounded-md"
          />
        ) : (
          <span className="text-2xl">⚡</span>
        )}
      </header>

      {/* 内容 */}
      <div className="flex-1">
        {phase === "upload" && (
          <Uploader onGenerate={handleGenerate} loading={loading} />
        )}

        {(phase === "processing" || phase === "failed") && (
          <ProgressView
            progress={job?.progress ?? 0}
            stage={job?.stage ?? "uploaded"}
            error={phase === "failed" ? error : null}
          />
        )}

        {phase === "done" && job && (
          <ResultView
            job={job}
            onRegenerating={handleRegenerating}
            onReset={handleReset}
          />
        )}
      </div>

      {phase === "failed" && (
        <button onClick={handleReset} className="btn-primary mt-4">
          重新开始
        </button>
      )}

      <footer className="pt-8 text-center text-[11px] text-gray-300">
        零门槛 · 零剪辑 · 30 秒生成竖屏爆款视频
      </footer>
    </main>
  );
}
