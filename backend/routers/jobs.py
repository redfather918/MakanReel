"""任务路由：触发生成、查询状态、换风格重生。"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from models import GenerateRequest, RegenerateRequest
from services import task_manager

router = APIRouter()


@router.post("/jobs/{job_id}/generate", status_code=202)
async def generate(job_id: str, body: GenerateRequest | None = None):
    job = task_manager.get_job(job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")
    if job.status == "processing":
        raise HTTPException(409, "任务正在生成中")
    if job.status != "uploaded" and job.status != "failed":
        # 已完成则允许重生
        pass

    template_id = body.template if body else None
    if template_id:
        if task_manager.get_template(template_id) is None:
            raise HTTPException(400, f"模板不存在: {template_id}")

    task_manager.start_pipeline(job_id, template_id)
    return {"job_id": job_id, "status": "processing", "template": template_id or "auto"}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = task_manager.get_job(job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")

    # 视频与缩略图 URL（相对路径，前端 BASE 已包含 /api，故这里不再带 /api）
    video_url = f"/assets/{job_id}/video" if job.video_path else None
    thumb_url = f"/assets/{job_id}/thumbnail" if job.thumbnail_path else None

    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "video_url": video_url,
        "thumbnail_url": thumb_url,
        "caption": job.caption,
        "hashtags": job.hashtags,
        "template": job.template,
        "note": job.note,
        "assets_count": len(job.assets),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "error": job.error,
    }


@router.get("/jobs")
async def list_jobs():
    jobs = task_manager.list_jobs()
    return [
        {
            "job_id": j.job_id,
            "status": j.status,
            "template": j.template,
            "note": j.note,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "assets_count": len(j.assets),
        }
        for j in jobs
    ]


@router.post("/jobs/{job_id}/regenerate", status_code=202)
async def regenerate(job_id: str, body: RegenerateRequest | None = None):
    job = task_manager.get_job(job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")
    if not job.assets:
        raise HTTPException(400, "无原始素材，无法重生")

    template_id = body.template if body else None
    if template_id and task_manager.get_template(template_id) is None:
        raise HTTPException(400, f"模板不存在: {template_id}")

    # 重置状态，复用已有素材
    job.status = "uploaded"
    job.stage = "uploaded"
    job.progress = 0
    job.error = None
    job.video_path = ""
    job.thumbnail_path = ""
    if template_id:
        job.template = template_id
    task_manager._save(job)

    # 强制使用新模板（传 None 时由流水线自动选不同的）
    task_manager.start_pipeline(job_id, template_id)
    return {"job_id": job_id, "status": "processing", "template": template_id or "auto"}
