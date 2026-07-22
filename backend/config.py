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
BACKGROUND_DIR = ASSETS_DIR / "backgrounds"

# 品牌视觉资产（Phase 2.1）
# Logo 默认指向 assets/logo.png；设为空字符串可关闭品牌角标叠加。
BRAND_LOGO_PATH = os.getenv("BRAND_LOGO_PATH", str(ASSETS_DIR / "logo.png"))
BRAND_LOGO_OPACITY = float(os.getenv("BRAND_LOGO_OPACITY", "0.9"))   # 角标透明度
BRAND_LOGO_SCALE = float(os.getenv("BRAND_LOGO_SCALE", "0.15"))     # 角标宽度占视频宽度比例
BRAND_LOGO_MARGIN = float(os.getenv("BRAND_LOGO_MARGIN", "0.04"))   # 角标距边缘边距占视频宽/高比例
BRAND_LOGO_DEFAULT_POS = os.getenv("BRAND_LOGO_DEFAULT_POS", "top-right")  # 模板未指定时的兜底位置

for d in (UPLOADS_DIR, RENDERS_DIR, JOBS_DIR, BGM_DIR, BACKGROUND_DIR):
    d.mkdir(parents=True, exist_ok=True)

# LLM 配置（OpenAI 兼容接口）
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 视觉增强
ENABLE_YOLO = os.getenv("ENABLE_YOLO", "false").lower() == "true"

# 智能抠图与背景替换（Phase 2.1 Matting & BG Replacement）
# 开启后，对上传素材做前景抠图并替换为品牌背景（默认 true，不增加门店操作步数）。
BACKGROUND_REPLACEMENT = os.getenv("BACKGROUND_REPLACEMENT", "true").lower() == "true"
BACKGROUND_DIR = ASSETS_DIR / "backgrounds"
BG_MODEL_PATH = os.getenv("BG_MODEL_PATH", str(ASSETS_DIR / "models" / "rmbg-1.4.onnx"))
BACKGROUND_DEFAULT_STYLE = os.getenv("BACKGROUND_DEFAULT_STYLE", "summer_cool")

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
