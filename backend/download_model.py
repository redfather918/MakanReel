"""一键下载 RMBG-1.4 ONNX 抠图模型权重。

用法:
    cd backend
    python download_model.py

下载来源: HuggingFace briaai/RMBG-1.4 (onnx/model.onnx, ~176MB)
保存位置: backend/assets/models/rmbg-1.4.onnx
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import config

TARGET = Path(config.BG_MODEL_PATH)
REPO_ID = "briaai/RMBG-1.4"
HF_FILENAME = "onnx/model.onnx"
FALLBACK_URL = "https://huggingface.co/briaai/RMBG-1.4/resolve/main/onnx/model.onnx"
EXPECTED_BYTES = 176_153_355  # 官方 ONNX 大致大小，仅做完整性参考


def _download_hf() -> None:
    """优先用 huggingface_hub 下载（支持缓存、断点续传、镜像）。"""
    from huggingface_hub import hf_hub_download

    print(f"[download] 使用 huggingface_hub 下载 {REPO_ID}/{HF_FILENAME}")
    cached = hf_hub_download(repo_id=REPO_ID, filename=HF_FILENAME, resume_download=True)
    cached_path = Path(cached)
    print(f"[download] 缓存文件: {cached_path}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    # 复制到目标位置
    import shutil
    shutil.copy2(cached_path, TARGET)


def _download_urllib() -> None:
    """备选：用 urllib 直接下载。"""
    import urllib.request

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    print(f"[download] 使用 urllib 直接下载 {FALLBACK_URL}")
    print(f"[download] 目标: {TARGET}")

    block = 8192
    downloaded = 0
    with urllib.request.urlopen(FALLBACK_URL, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        with open(TARGET, "wb") as f:
            while True:
                chunk = resp.read(block)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r[download] {downloaded}/{total} bytes ({pct}%)", end="")
    print()


def main() -> int:
    if TARGET.exists():
        size = TARGET.stat().st_size
        print(f"[download] 模型已存在: {TARGET} ({size / 1024 / 1024:.1f} MB)")
        if size < EXPECTED_BYTES * 0.9:
            print("[download] 文件大小异常，将重新下载")
            TARGET.unlink()
        else:
            print("[download] 大小正常，跳过下载")
            return 0

    try:
        _download_hf()
    except Exception as e:
        print(f"[download] huggingface_hub 失败，尝试 urllib: {e}")
        _download_urllib()

    if not TARGET.exists():
        print("[download] 错误：下载后仍未找到模型文件", file=sys.stderr)
        return 1

    actual_size = TARGET.stat().st_size
    print(f"[download] 完成: {TARGET} ({actual_size / 1024 / 1024:.1f} MB)")
    if actual_size < EXPECTED_BYTES * 0.5:
        print("[download] 警告：文件大小明显偏小，可能下载不完整", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
