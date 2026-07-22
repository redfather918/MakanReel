"""资产路由：下载视频、缩略图。"""
from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services import task_manager

router = APIRouter()


@router.get("/assets/{job_id}/video")
async def download_video(job_id: str):
    job = task_manager.get_job(job_id)
    if job is None or not job.video_path:
        raise HTTPException(404, "视频不存在或未生成完成")
    p = Path(job.video_path)
    if not p.exists():
        raise HTTPException(404, "视频文件丢失")
    return FileResponse(
        str(p), media_type="video/mp4",
        filename=f"{job_id}.mp4",
    )


@router.get("/assets/{job_id}/thumbnail")
async def get_thumbnail(job_id: str):
    job = task_manager.get_job(job_id)
    if job is None or not job.thumbnail_path:
        raise HTTPException(404, "缩略图不存在")
    p = Path(job.thumbnail_path)
    if not p.exists():
        raise HTTPException(404, "缩略图文件丢失")
    return FileResponse(str(p), media_type="image/jpeg")
