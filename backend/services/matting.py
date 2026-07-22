"""智能抠图与背景替换（Phase 2.1 Matting & BG Replacement）。

优先用 RMBG-1.4 ONNX 模型推理前景 alpha，合成到品牌背景；
模型不可用时降级为 OpenCV 谱残差显著性软抠图，保证功能始终可用。
"""
from __future__ import annotations

import os

import cv2
import numpy as np

import config

_SESSION = None
_SESSION_ERROR = False


def _get_session():
    """惰性加载 RMBG-1.4 ONNX 推理会话；失败/缺失则降级返回 None。"""
    global _SESSION, _SESSION_ERROR
    if _SESSION is not None:
        return _SESSION
    if _SESSION_ERROR:
        return None
    if not os.path.exists(config.BG_MODEL_PATH):
        print(f"[matting] 模型不存在 {config.BG_MODEL_PATH}，降级显著性软抠图")
        _SESSION_ERROR = True
        return None
    try:
        import onnxruntime as ort

        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        _SESSION = ort.InferenceSession(
            config.BG_MODEL_PATH, sess_options=so, providers=["CPUExecutionProvider"]
        )
        print("[matting] ONNX 模型加载成功")
        return _SESSION
    except Exception as e:  # pragma: no cover - 依赖/权重异常
        print(f"[matting] ONNX 加载失败，降级: {e}")
        _SESSION_ERROR = True
        return None


def _infer_alpha(session, img_rgb: np.ndarray) -> np.ndarray:
    """RMBG-1.4 推理前景概率，返回与原图同尺寸软 alpha (0-255 uint8)。"""
    h, w = img_rgb.shape[:2]
    size = 1024
    resized = cv2.resize(img_rgb, (size, size), interpolation=cv2.INTER_AREA)
    arr = resized.astype(np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)[None, ...]
    input_name = session.get_inputs()[0].name
    out = session.run(None, {input_name: arr})[0]
    alpha = out[0, 0]
    lo, hi = float(alpha.min()), float(alpha.max())
    alpha = (alpha - lo) / (hi - lo + 1e-8)
    alpha = (alpha * 255).astype(np.uint8)
    alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_LINEAR)
    # 轻微羽化，使前景边缘更自然
    alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=1.5)
    return alpha


def _saliency_alpha(img_bgr: np.ndarray) -> np.ndarray:
    """OpenCV 谱残差显著性兜底：生成前景 alpha（无 ONNX 时使用）。

    流程：显著性图 → Otsu 二值化 → 形态学清理 → 放大羽化。
    效果弱于 RMBG，但模型缺失时仍能保留主体并替换背景。
    """
    h, w = img_bgr.shape[:2]
    small = cv2.resize(img_bgr, (64, 64), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray -= gray.mean()
    fft = np.fft.fft2(gray)
    mag = np.abs(fft)
    phase = np.angle(fft)
    log_mag = np.log(mag + 1e-8)
    avg = cv2.boxFilter(log_mag, -1, (3, 3))
    residual = log_mag - avg
    sal = np.abs(np.fft.ifft2(np.exp(residual) * np.exp(1j * phase))) ** 2
    sal = (sal - sal.min()) / (sal.max() - sal.min() + 1e-8)
    sal = cv2.GaussianBlur(sal, (9, 9), 0)

    # Otsu 二值化 + 形态学清理（去噪 + 填洞）
    sal_u8 = (sal * 255).astype(np.uint8)
    _, mask = cv2.threshold(sal_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 放大并羽化边缘
    alpha = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=8)
    return alpha


def _cover_resize(bg: np.ndarray, w: int, h: int) -> np.ndarray:
    """按比例铺满 (w,h)，无拉伸，居中裁剪。"""
    bh, bw = bg.shape[:2]
    scale = max(w / bw, h / bh)
    nw, nh = max(1, int(round(bw * scale))), max(1, int(round(bh * scale)))
    bg = cv2.resize(bg, (nw, nh), interpolation=cv2.INTER_AREA)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return bg[y:y + h, x:x + w]


def _load_background(style: str, h: int, w: int) -> np.ndarray:
    """加载指定风格品牌背景；文件不存在则程序化生成渐变。返回 BGR (h,w,3)。"""
    path = config.BACKGROUND_DIR / f"{style}.png"
    if path.exists():
        bg = cv2.imread(str(path))
        if bg is not None:
            return _cover_resize(bg, w, h)
    # 程序化兜底（蓝绿清凉渐变）
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = yy / h * 0.6 + xx / w * 0.4
    img = np.zeros((h, w, 3), np.float32)
    img[:, :, 0] = 30 + 40 * g
    img[:, :, 1] = 120 + 80 * g
    img[:, :, 2] = 160 + 60 * (1 - g)
    return img.astype(np.uint8)


def _composite(fg_bgr: np.ndarray, alpha: np.ndarray, bg_bgr: np.ndarray) -> np.ndarray:
    """按 alpha 将前景合成到背景上，返回 BGR。"""
    a = alpha.astype(np.float32) / 255.0
    a = a[:, :, None]
    out = fg_bgr.astype(np.float32) * a + bg_bgr.astype(np.float32) * (1 - a)
    return out.astype(np.uint8)


def remove_bg_to_background(img_bgr: np.ndarray, style: str | None = None) -> np.ndarray:
    """抠图并替换为品牌背景。

    返回合成后的 BGR 图（与原图同尺寸）。
    config.BACKGROUND_REPLACEMENT 关闭时直接返回原图。
    """
    if not config.BACKGROUND_REPLACEMENT:
        return img_bgr
    style = style or config.BACKGROUND_DEFAULT_STYLE
    h, w = img_bgr.shape[:2]

    session = _get_session()
    if session is not None:
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        alpha = _infer_alpha(session, rgb)
    else:
        alpha = _saliency_alpha(img_bgr)

    bg = _load_background(style, h, w)
    return _composite(img_bgr, alpha, bg)
