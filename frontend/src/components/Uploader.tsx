"use client";

import { useRef, useState } from "react";

interface UploaderProps {
  onGenerate: (files: File[], note: string) => void;
  loading: boolean;
}

const MAX = 3;

export default function Uploader({ onGenerate, loading }: UploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [dragOver, setDragOver] = useState(false);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const arr = Array.from(list).slice(0, MAX - files.length);
    const next = [...files, ...arr].slice(0, MAX);
    setFiles(next);
    setPreviews(next.map((f) => URL.createObjectURL(f)));
  }

  function removeAt(i: number) {
    URL.revokeObjectURL(previews[i]);
    const nf = files.filter((_, idx) => idx !== i);
    setFiles(nf);
    setPreviews(nf.map((f) => URL.createObjectURL(f)));
  }

  return (
    <div className="space-y-5">
      {/* 上传区 */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        className={`flex min-h-[180px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-6 text-center transition ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-gray-300 bg-white"
        }`}
      >
        <div className="text-5xl">📸</div>
        <p className="mt-3 text-base font-semibold text-gray-800">
          点击 / 拖拽上传素材
        </p>
        <p className="mt-1 text-xs text-gray-500">
          1~3 张图片 (JPEG/PNG/HEIC) 或 1 段短视频 (MP4/MOV)
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/heic,.heic,.heif,video/mp4,video/quicktime,.mp4,.mov"
          multiple
          capture="environment"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {/* 预览缩略图 */}
      {previews.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {previews.map((src, i) => (
            <div key={i} className="group relative aspect-[9/16] overflow-hidden rounded-xl bg-gray-100 ring-1 ring-black/5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="" className="h-full w-full object-cover" />
              <button
                onClick={() => removeAt(i)}
                className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-xs text-white"
              >
                ✕
              </button>
              <span className="absolute bottom-1 left-1 rounded bg-black/50 px-1.5 py-0.5 text-[10px] text-white">
                {files[i].type.startsWith("video") ? "视频" : `图 ${i + 1}`}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* 备注 */}
      <div>
        <label className="mb-1.5 block text-sm font-semibold text-gray-700">
          产品 / 活动备注 <span className="font-normal text-gray-400">(可选)</span>
        </label>
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="例：芒果啵啵 买一送一"
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-base outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
        />
      </div>

      {/* 生成按钮 */}
      <button
        disabled={files.length === 0 || loading}
        onClick={() => onGenerate(files, note)}
        className="btn-primary"
      >
        {loading ? "处理中…" : "✨ AI 一键生成爆款视频"}
      </button>
      <p className="text-center text-xs text-gray-400">
        上传即表示原画质传输，30 秒内生成竖屏短视频
      </p>
    </div>
  );
}
