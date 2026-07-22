"""Pydantic 数据模型：对应 TRD 第 5 章。"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Asset(BaseModel):
    id: str
    name: str
    type: str = Field(description="image | video")
    orig_path: str
    size: int = 0


class Segment(BaseModel):
    duration: float = 2.0
    effect: str = "ken_burns"
    overlay_text: Optional[str] = None


class Template(BaseModel):
    id: str
    name: str
    duration: float = 8.0
    bgm: str = ""
    segments: list[Segment] = Field(default_factory=list)
    hook_text: str = ""
    hook_duration: float = 2.5
    transition: str = "fade"
    logo_position: str = "top-right"
    style_prompt: str = ""


class Job(BaseModel):
    job_id: str
    status: str = "uploaded"          # uploaded | processing | done | failed
    stage: str = "uploaded"            # preprocessing | composing | caption | done
    progress: int = 0
    note: str = ""
    assets: list[Asset] = Field(default_factory=list)
    processed: list[str] = Field(default_factory=list)
    template: str = ""
    video_path: str = ""
    thumbnail_path: str = ""
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class GenerateRequest(BaseModel):
    template: Optional[str] = None


class RegenerateRequest(BaseModel):
    template: Optional[str] = None
