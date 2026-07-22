"""AI 智能预处理引擎：智能裁切 9:16 + 画质修复 + (可选)背景纯化。

对应 TRD 3.2 模块二。
默认基于 OpenCV 显著性检测 + 人脸 Haar 级联做主体定位；
ENABLE_YOLO=true 时用 YOLOv8 增强（识别杯/瓶/人）。
"""
from __future__ import annotations
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

import config
from services import matting

# 人脸检测级联（OpenCV 4.x 可用；5.0 已移除 Haar API，此时降级为 None）
_FACE_CASCADE: cv2.CascadeClassifier | None = None
_FACE_CASCADE_UNAVAILABLE = not hasattr(cv2, "CascadeClassifier")
_YOLO = None


def _get_face_cascade() -> cv2.CascadeClassifier | None:
    global _FACE_CASCADE
    if _FACE_CASCADE_UNAVAILABLE:
        return None
    if _FACE_CASCADE is None:
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
            if _FACE_CASCADE.empty():
                _FACE_CASCADE = None
        except Exception as e:
            print(f"[preprocessor] 人脸级联加载失败，降级: {e}")
            _FACE_CASCADE = None
    return _FACE_CASCADE


def _get_yolo():
    """惰性加载 YOLOv8，失败返回 None。"""
    global _YOLO
    if _YOLO is not None:
        return _YOLO if _YOLO else None
    if not config.ENABLE_YOLO:
        _YOLO = False
        return None
    try:
        from ultralytics import YOLO
        _YOLO = YOLO("yolov8n.pt")
        return _YOLO
    except Exception as e:
        print(f"[preprocessor] YOLO 加载失败，降级 OpenCV: {e}")
        _YOLO = False
        return None


# --------------------------------------------------------------------------- #
# 智能裁切 9:16
# --------------------------------------------------------------------------- #
def _saliency_center(img_bgr: np.ndarray) -> tuple[float, float]:
    """用谱残差 (Spectral Residual) 算法计算视觉重心，纯 numpy 实现。

    返回 (cx, cy) 归一化坐标 [0,1]。
    参考: Hou & Zhang, "Saliency Detection: A Spectral Residual Approach".
    """
    # 缩小到 64x64 加速并稳定频域分析
    small = cv2.resize(img_bgr, (64, 64), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray -= gray.mean()

    # FFT
    fft = np.fft.fft2(gray)
    magnitude = np.abs(fft)
    phase = np.angle(fft)
    log_mag = np.log(magnitude + 1e-8)
    # 谱残差 = log|F| - 平均滤波后的 log|F|
    avg = cv2.boxFilter(log_mag, -1, (3, 3))
    residual = log_mag - avg
    # 重建 saliency
    new_fft = np.exp(residual) * np.exp(1j * phase)
    sal = np.abs(np.fft.ifft2(new_fft)) ** 2
    sal = (sal - sal.min()) / (sal.max() - sal.min() + 1e-8)
    sal = cv2.GaussianBlur(sal, (9, 9), 0)

    total = sal.sum()
    if total <= 1e-6:
        return 0.5, 0.5
    ys, xs = np.indices(sal.shape)
    cx = float((xs * sal).sum() / total) / 64.0
    cy = float((ys * sal).sum() / total) / 64.0
    return cx, cy


def _face_center(img_bgr: np.ndarray) -> tuple[float, float] | None:
    """人脸检测，返回最大人脸中心归一化坐标，无人脸或检测不可用返回 None。"""
    cascade = _get_face_cascade()
    if cascade is None:
        return None
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
    if len(faces) == 0:
        return None
    # 取最大脸
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (x + w / 2) / img_bgr.shape[1], (y + h / 2) / img_bgr.shape[0]


def _yolo_center(img_bgr: np.ndarray) -> tuple[float, float] | None:
    """YOLOv8 检测主体（人/杯/瓶/食物），返回中心坐标。"""
    model = _get_yolo()
    if model is None:
        return None
    try:
        res = model(img_bgr, verbose=False)
        # 目标类别：person(0), cup(41), bottle(39), bowl(45), food 相关
        keep_cls = {0, 39, 41, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55}
        best = None
        best_area = 0
        for box in res[0].boxes:
            if int(box.cls) in keep_cls:
                area = float(box.conf) * (box.xywh[0][2] * box.xywh[0][3])
                if area > best_area:
                    best_area = area
                    best = box
        if best is None:
            return None
        cx, cy = best.xywh[0][0], best.xywh[0][1]
        return float(cx) / img_bgr.shape[1], float(cy) / img_bgr.shape[0]
    except Exception as e:
        print(f"[preprocessor] YOLO 推理失败: {e}")
        return None


def smart_crop_9_16(img_bgr: np.ndarray, target_w: int = 1080, target_h: int = 1920) -> np.ndarray:
    """以主体为中心裁切 9:16，保证关键要素不被切掉。"""
    h, w = img_bgr.shape[:2]
    target_ratio = target_w / target_h  # 0.5625
    src_ratio = w / h

    # 确定主体中心：YOLO > 人脸 > 显著性
    cx_n, cy_n = _saliency_center(img_bgr)
    face = _face_center(img_bgr)
    if face:
        cx_n, cy_n = face
    yolo = _yolo_center(img_bgr)
    if yolo:
        cx_n, cy_n = yolo

    if src_ratio > target_ratio:
        # 横向偏宽 → 左右裁切
        new_w = int(h * target_ratio)
        new_h = h
    else:
        # 竖向偏高 → 上下裁切
        new_w = w
        new_h = int(w / target_ratio)

    new_w = min(new_w, w)
    new_h = min(new_h, h)

    cx = int(cx_n * w)
    cy = int(cy_n * h)
    x1 = max(0, min(cx - new_w // 2, w - new_w))
    y1 = max(0, min(cy - new_h // 2, h - new_h))

    cropped = img_bgr[y1:y1 + new_h, x1:x1 + new_w]
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)


# --------------------------------------------------------------------------- #
# 画质修复
# --------------------------------------------------------------------------- #
def enhance(img_bgr: np.ndarray) -> np.ndarray:
    """CLAHE 对比度增强 + 饱和度提升 + 去噪。"""
    # 去噪
    img = cv2.fastNlMeansDenoisingColored(img_bgr, None, 5, 5, 7, 21)
    # CLAHE 亮度通道
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # 饱和度提升（提亮饮品色彩）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = cv2.add(s, 25)
    s = np.clip(s, 0, 255).astype(np.uint8)
    v = cv2.add(v, 10)
    v = np.clip(v, 0, 255).astype(np.uint8)
    hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return img


# --------------------------------------------------------------------------- #
# 对外入口
# --------------------------------------------------------------------------- #
def _load_image_bgr(path: str) -> np.ndarray:
    """支持 HEIC 等格式：用 PIL 读取再转 BGR。"""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # 修正方向
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img)[:, :, ::-1]  # RGB -> BGR
    return arr


def process_image(path: str, out_path: str, idx: int, background: str | None = None) -> str:
    """处理单张图片：抠图换背景 → 裁切 9:16 + 画质修复 → 保存 1080x1920 JPEG。

    background: 指定品牌背景风格（None 时用 config.BACKGROUND_DEFAULT_STYLE）。
    config.BACKGROUND_REPLACEMENT 关闭时跳过换背景。
    """
    bgr = _load_image_bgr(path)
    if config.BACKGROUND_REPLACEMENT:
        bgr = matting.remove_bg_to_background(bgr, background)
    cropped = smart_crop_9_16(bgr, config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT)
    enhanced = enhance(cropped)
    cv2.imwrite(out_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"[preprocessor] 图片 {idx} 处理完成 -> {out_path}")
    return out_path


def process_video(path: str, out_dir: str, max_seconds: int = 5) -> list[str]:
    """从视频中均匀抽取关键帧并处理，返回处理后图片路径列表。"""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if fps else 0
    # 截取前 max_seconds 秒
    usable = min(duration, max_seconds) if duration else max_seconds
    n_frames = 3
    timestamps = [usable * (i + 0.5) / n_frames for i in range(n_frames)]
    results: list[str] = []
    for i, t in enumerate(timestamps):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, frame = cap.read()
        if not ok:
            continue
        cropped = smart_crop_9_16(frame, config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT)
        enhanced = enhance(cropped)
        out_path = os.path.join(out_dir, f"vframe_{i}.jpg")
        cv2.imwrite(out_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 92])
        results.append(out_path)
    cap.release()
    if not results:
        # 兜底：读首帧
        cap = cv2.VideoCapture(path)
        ok, frame = cap.read()
        cap.release()
        if ok:
            cropped = smart_crop_9_16(frame, config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT)
            out_path = os.path.join(out_dir, "vframe_0.jpg")
            cv2.imwrite(out_path, enhance(cropped), [cv2.IMWRITE_JPEG_QUALITY, 92])
            results.append(out_path)
    print(f"[preprocessor] 视频抽帧 {len(results)} 张")
    return results


def process_all(asset_paths: list[tuple[str, str]], out_dir: str,
                background: str | None = None) -> list[str]:
    """处理所有素材。

    asset_paths: [(type, path), ...]  type 为 'image' 或 'video'
    background: 背景替换风格（仅图片生效；空/None 用 config 默认）。
    返回处理后图片路径列表（统一为 1080x1920 JPEG）。
    """
    processed: list[str] = []
    idx = 0
    for typ, path in asset_paths:
        if typ == "video":
            frames = process_video(path, out_dir)
            processed.extend(frames)
            idx += len(frames)
        else:
            out_path = os.path.join(out_dir, f"img_{idx}.jpg")
            process_image(path, out_path, idx, background)
            processed.append(out_path)
            idx += 1
    return processed
