"""上传路由：接收 1~3 张图片或 1 段短视频，存储原文件，创建 Job。"""
from __future__ import annotations
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

import config
from models import Job, Asset
from services import task_manager

router = APIRouter()

IMG_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
VID_EXTS = {".mp4", ".mov", ".m4v"}


@router.post("/upload", status_code=201)
async def upload(
    files: list[UploadFile] = File(...),
    note: str = Form(""),
):
    if not files:
        raise HTTPException(400, "至少上传 1 个素材")
    if len(files) > config.MAX_IMAGES + 1:
        raise HTTPException(400, f"最多 {config.MAX_IMAGES} 张图片或 1 段视频")

    job_id = f"j_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    job_dir = config.UPLOADS_DIR / job_id / "orig"
    job_dir.mkdir(parents=True, exist_ok=True)

    assets: list[Asset] = []
    video_count = 0
    img_count = 0

    for i, f in enumerate(files):
        ext = Path(f.filename or "").suffix.lower()
        if ext in IMG_EXTS:
            if img_count >= config.MAX_IMAGES:
                continue
            ftype = "image"
            img_count += 1
        elif ext in VID_EXTS:
            if video_count >= 1:
                continue
            ftype = "video"
            video_count += 1
        else:
            raise HTTPException(400, f"不支持的格式: {ext}")

        data = await f.read()
        if ftype == "image" and len(data) > config.MAX_IMAGE_SIZE:
            raise HTTPException(400, f"{f.filename} 超过 {config.MAX_IMAGE_SIZE // 1024 // 1024}MB")
        if ftype == "video" and len(data) > config.MAX_VIDEO_SIZE:
            raise HTTPException(400, f"{f.filename} 超过 {config.MAX_VIDEO_SIZE // 1024 // 1024}MB")

        safe_name = f"{i}_{f.filename}".replace(" ", "_")
        out_path = job_dir / safe_name
        out_path.write_bytes(data)
        assets.append(Asset(
            id=f"a_{i}", name=f.filename or safe_name, type=ftype,
            orig_path=str(out_path), size=len(data),
        ))

    if not assets:
        raise HTTPException(400, "未保存任何有效素材")

    job = Job(
        job_id=job_id, status="uploaded", stage="uploaded",
        progress=0, note=note or "", assets=assets,
    )
    task_manager._save(job)
    return {
        "job_id": job_id,
        "assets": [a.model_dump() for a in assets],
        "note": note or "",
        "status": "uploaded",
    }
