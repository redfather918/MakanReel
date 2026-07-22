"use client";

interface ProgressViewProps {
  progress: number;
  stage: string;
  error: string | null;
}

const STAGE_LABELS: Record<string, string> = {
  uploaded: "排队中…",
  preprocessing: "AI 智能裁切与画质修复…",
  composing: "卡点视频合成中…",
  caption: "生成新加坡本地化文案…",
  done: "完成！",
};

export default function ProgressView({ progress, stage, error }: ProgressViewProps) {
  return (
    <div className="flex flex-col items-center py-10 text-center">
      <div className="relative flex h-24 w-24 items-center justify-center">
        <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="44" fill="none" stroke="#f3e8d8" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="#f97316"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 44}`}
            strokeDashoffset={`${2 * Math.PI * 44 * (1 - progress / 100)}`}
            className="transition-all duration-500"
          />
        </svg>
        <span className="absolute text-xl font-bold text-brand-600">{progress}%</span>
      </div>

      {error ? (
        <div className="mt-6 max-w-sm rounded-2xl bg-red-50 p-4 text-sm text-red-600 ring-1 ring-red-200">
          <p className="font-semibold">生成失败</p>
          <p className="mt-1 break-words">{error}</p>
        </div>
      ) : (
        <p className="mt-6 text-base font-semibold text-gray-700">
          {STAGE_LABELS[stage] || stage}
        </p>
      )}
      <p className="mt-2 max-w-xs text-xs text-gray-400">
        后台静默运行：画质修复 · 智能裁切 · 卡点合成 · AI 文案
      </p>
    </div>
  );
}
