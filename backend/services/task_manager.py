"""任务管理器：编排 预处理 → 视频合成 → 文案生成 的异步流水线。

对应 TRD 3.2-3.4。Phase 1 用 asyncio 后台任务，内存字典 + JSON 持久化。
"""
from __future__ import annotations
import asyncio
import json
from datetime import datetime
from pathlib import Path

import config
from models import Job, Asset, Template
from services import preprocessor, video_renderer, caption_writer

# 内存任务表
_jobs: dict[str, Job] = {}


# --------------------------------------------------------------------------- #
# 持久化
# --------------------------------------------------------------------------- #
def _job_file(job_id: str) -> Path:
    return config.JOBS_DIR / f"{job_id}.json"


def _save(job: Job) -> None:
    _jobs[job.job_id] = job
    _job_file(job.job_id).write_text(job.model_dump_json(indent=2), encoding="utf-8")


def _load(job_id: str) -> Job | None:
    if job_id in _jobs:
        return _jobs[job_id]
    f = _job_file(job_id)
    if f.exists():
        job = Job.model_validate_json(f.read_text(encoding="utf-8"))
        _jobs[job_id] = job
        return job
    return None


def get_job(job_id: str) -> Job | None:
    return _load(job_id)


def list_jobs() -> list[Job]:
    # 合并内存与磁盘
    seen: set[str] = set()
    result: list[Job] = []
    for j in _jobs.values():
        seen.add(j.job_id)
        result.append(j)
    for f in config.JOBS_DIR.glob("*.json"):
        jid = f.stem
        if jid not in seen:
            j = _load(jid)
            if j:
                result.append(j)
    result.sort(key=lambda j: j.created_at, reverse=True)
    return result


# --------------------------------------------------------------------------- #
# 模板加载
# --------------------------------------------------------------------------- #
def _load_templates() -> dict[str, Template]:
    data = json.loads(config.TEMPLATES_FILE.read_text(encoding="utf-8"))
    return {t["id"]: Template(**t) for t in data}


def get_templates() -> list[Template]:
    return list(_load_templates().values())


def get_template(tid: str) -> Template | None:
    return _load_templates().get(tid)


# --------------------------------------------------------------------------- #
# 流水线
# --------------------------------------------------------------------------- #
def _update(job: Job, status: str = None, stage: str = None, progress: int = None,
            error: str = None) -> None:
    if status:
        job.status = status
    if stage:
        job.stage = stage
    if progress is not None:
        job.progress = progress
    if error is not None:
        job.error = error
    job.updated_at = datetime.now()
    _save(job)


async def run_pipeline(job_id: str, template_id: str | None) -> None:
    """异步执行完整生成流水线。"""
    job = _load(job_id)
    if job is None:
        return

    templates = _load_templates()
    # 选模板：指定 > 上次 > 随机
    if template_id and template_id in templates:
        tpl = templates[template_id]
    elif job.template and job.template in templates:
        tpl = templates[job.template]
    else:
        # 选与上次不同的
        import random
        ids = [i for i in templates if i != job.template] or list(templates)
        tpl = templates[random.choice(ids)]
    job.template = tpl.id

    try:
        _update(job, status="processing", stage="preprocessing", progress=5)

        job_dir = config.UPLOADS_DIR / job_id
        proc_dir = job_dir / "processed"
        proc_dir.mkdir(parents=True, exist_ok=True)

        # 1. 预处理
        asset_paths = [(a.type, a.orig_path) for a in job.assets]
        processed = await asyncio.to_thread(
            preprocessor.process_all, asset_paths, str(proc_dir), tpl.background
        )
        job.processed = processed
        _update(job, stage="preprocessing", progress=40)

        # 2. 视频合成
        _update(job, stage="composing", progress=50)
        render_dir = config.RENDERS_DIR / job_id
        render_dir.mkdir(parents=True, exist_ok=True)
        video_path, thumb_path = await asyncio.to_thread(
            video_renderer.render, processed, tpl, str(render_dir), job.note
        )
        job.video_path = video_path
        job.thumbnail_path = thumb_path
        _update(job, stage="composing", progress=85)

        # 3. 文案生成
        _update(job, stage="caption", progress=90)
        caption, hashtags = await asyncio.to_thread(
            caption_writer.generate_caption, job.note, tpl.style_prompt
        )
        job.caption = caption
        job.hashtags = hashtags

        _update(job, status="done", stage="done", progress=100)
        print(f"[task] 任务 {job_id} 完成")

    except Exception as e:
        import traceback
        traceback.print_exc()
        _update(job, status="failed", error=str(e))
        print(f"[task] 任务 {job_id} 失败: {e}")


def start_pipeline(job_id: str, template_id: str | None) -> None:
    """启动后台任务（非阻塞）。"""
    asyncio.create_task(run_pipeline(job_id, template_id))
