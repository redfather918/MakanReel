"""生成 Phase 2.1 品牌背景 PNG 到 backend/assets/backgrounds/。

三种风格（与模板风格匹配）：
- summer_cool   清凉夏日：青蓝渐变 + 柔光斑，适配多数饮品模板
- neon_night    霓虹夜店：深紫黑 + 霓虹光条，适配 night_vibe 模板
- minimal_brand 极简品牌：白底 + 品牌橙 #FF6B35 几何，适配高质感模板

纯 numpy + cv2 程序化生成，零外部图片依赖。
"""
from __future__ import annotations

import numpy as np
import cv2
from pathlib import Path

H, W = 1080, 1920
OUT = Path(__file__).resolve().parent / "assets" / "backgrounds"
OUT.mkdir(parents=True, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
t = yy / H * 0.6 + xx / W * 0.4  # 对角渐变系数


def save(name: str, img: np.ndarray) -> None:
    cv2.imwrite(str(OUT / f"{name}.png"), img)
    print(f"[bg] 生成 {name}.png {img.shape[1]}x{img.shape[0]}")


# 1. summer_cool —— 清凉夏日
img = np.zeros((H, W, 3), np.float32)
img[:, :, 0] = 20 + 60 * t        # B
img[:, :, 1] = 150 + 70 * t       # G
img[:, :, 2] = 200 - 80 * t       # R
for cx, cy, r, bright in [(300, 400, 260, 45), (820, 1200, 320, 55), (520, 1650, 200, 35)]:
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    spot = np.clip(1 - d / r, 0, 1) ** 2 * bright
    img[:, :, :] += spot[:, :, None]
save("summer_cool", np.clip(img, 0, 255).astype(np.uint8))

# 2. neon_night —— 霓虹夜店
img = np.zeros((H, W, 3), np.float32)
img[:, :, 0] = 10 + 20 * t
img[:, :, 1] = 5 + 10 * t
img[:, :, 2] = 20 + 40 * (1 - t)
for off, col in [(0, (255, 40, 200)), (430, (40, 200, 255)), (900, (200, 40, 255))]:
    band = np.abs(((xx - yy * 0.3 + off) % 640) - 320)
    mask = np.clip(1 - band / 45, 0, 1)
    img[:, :, 0] += col[0] * mask * 0.5
    img[:, :, 1] += col[1] * mask * 0.5
    img[:, :, 2] += col[2] * mask * 0.5
save("neon_night", np.clip(img, 0, 255).astype(np.uint8))

# 3. minimal_brand —— 极简品牌（品牌橙 #FF6B35 -> BGR 53,107,255）
img = np.full((H, W, 3), 245, np.float32)
img[: H // 2, :] = [220, 235, 255]
img[H * 3 // 4:, :] = [40, 100, 255]
Y, X = np.ogrid[0:H, 0:W]
d = np.sqrt((X - W // 2) ** 2 + (Y - H // 2) ** 2)
img[d < 200] = [53, 107, 255]
save("minimal_brand", np.clip(img, 0, 255).astype(np.uint8))

print("[bg] 完成")
