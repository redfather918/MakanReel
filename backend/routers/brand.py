"""品牌配置路由（Phase 2.1）：查看/更新品牌 Logo 与角标策略。

对应 PRD 7.1.1「后台可配 Logo 图与位置」。
"""
from __future__ import annotations
import os

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

import config

router = APIRouter()


@router.get("/brand")
async def get_brand():
    """返回当前品牌视觉配置。"""
    enabled = bool(config.BRAND_LOGO_PATH) and os.path.exists(config.BRAND_LOGO_PATH)
    return {
        "enabled": enabled,
        "logo_url": "/brand/logo" if enabled else None,
        "position": config.BRAND_LOGO_DEFAULT_POS,
        "opacity": config.BRAND_LOGO_OPACITY,
        "scale": config.BRAND_LOGO_SCALE,
        "margin": config.BRAND_LOGO_MARGIN,
    }


@router.get("/brand/logo")
async def get_brand_logo():
    """直接取品牌 Logo 图片（供前端展示）。"""
    if not config.BRAND_LOGO_PATH or not os.path.exists(config.BRAND_LOGO_PATH):
        raise HTTPException(404, "尚未配置品牌 Logo")
    return FileResponse(config.BRAND_LOGO_PATH, media_type="image/png")


@router.post("/brand/logo", status_code=200)
async def upload_brand_logo(file: UploadFile = File(...)):
    """上传/更新品牌 Logo（覆盖 assets/logo.png）。

    要求 PNG 透明背景；建议宽高比 3:1 左右、预留右侧留白。
    """
    if not config.BRAND_LOGO_PATH:
        raise HTTPException(400, "BRAND_LOGO_PATH 未配置，无法写入")
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(400, "仅支持 png/jpg/webp/svg 格式")

    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Logo 超过 5MB")

    # 始终以 .png 落盘（保持后端叠加逻辑统一）
    out_path = os.path.splitext(config.BRAND_LOGO_PATH)[0] + ".png"
    with open(out_path, "wb") as f:
        f.write(data)

    print(f"[brand] Logo 已更新 -> {out_path}")
    return {
        "ok": True,
        "logo_url": "/brand/logo",
        "size": len(data),
    }
