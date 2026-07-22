"""AI 短视频内容生成 Portal —— FastAPI 后端入口。

启动: uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import upload, jobs, assets, templates


# 注册 HEIC 支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception as e:
    print(f"[main] HEIC 支持未启用: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[main] 存储目录: {config.STORAGE_DIR}")
    print(f"[main] LLM: {config.LLM_MODEL} @ {config.LLM_API_BASE} (key={'已配置' if config.LLM_API_KEY else '未配置-模板兜底'})")
    print(f"[main] YOLO 增强: {'开启' if config.ENABLE_YOLO else '关闭'}")
    yield


app = FastAPI(
    title="AI 短视频内容生成 Portal API",
    version="1.0.0",
    description="新加坡餐饮品牌 AI 短视频生成后端 (Phase 1)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(assets.router, prefix="/api", tags=["assets"])
app.include_router(templates.router, prefix="/api", tags=["templates"])


@app.get("/")
async def root():
    return {"service": "AI Video Portal API", "version": "1.0.0", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
