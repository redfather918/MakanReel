"""应用配置：从环境变量读取，提供合理默认值。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / os.getenv("STORAGE_DIR", "storage")
UPLOADS_DIR = STORAGE_DIR / "uploads"
RENDERS_DIR = STORAGE_DIR / "renders"
JOBS_DIR = STORAGE_DIR / "data" / "jobs"
TEMPLATES_FILE = BASE_DIR / "templates_data" / "templates.json"
BGM_DIR = BASE_DIR / "templates_data" / "bgm"
ASSETS_DIR = BASE_DIR / "assets"

for d in (UPLOADS_DIR, RENDERS_DIR, JOBS_DIR, BGM_DIR):
    d.mkdir(parents=True, exist_ok=True)

# LLM 配置（OpenAI 兼容接口）
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 视觉增强
ENABLE_YOLO = os.getenv("ENABLE_YOLO", "false").lower() == "true"

# 服务
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# 限制
MAX_IMAGES = 3
MAX_IMAGE_SIZE = 20 * 1024 * 1024      # 20MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024      # 50MB
MAX_VIDEO_SECONDS = 10
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
