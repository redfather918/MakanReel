"""模板路由：返回可用模板列表。"""
from __future__ import annotations
from fastapi import APIRouter

from services import task_manager

router = APIRouter()


@router.get("/templates")
async def list_templates():
    tpls = task_manager.get_templates()
    return [
        {
            "id": t.id,
            "name": t.name,
            "duration": t.duration,
            "hook_text": t.hook_text,
            "style_prompt": t.style_prompt,
        }
        for t in tpls
    ]
