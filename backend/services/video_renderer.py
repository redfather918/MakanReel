"""FFmpeg 视频合成引擎：卡点拼接 + Ken Burns + 花字烧录 + BGM。

对应 TRD 3.3 模块三。
采用分阶段渲染（每段单独生成 → 拼接 → 加音频 → 烧字），保证 Windows 兼容与稳定性。
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

import config
from models import Template
from services import bgm_gen

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def _font_path() -> str:
    """查找可用字体文件，优先粗体。"""
    candidates = [
        config.ASSETS_DIR / "font" / "NotoSansSC-Bold.ttf",
        config.ASSETS_DIR / "font" / "font.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arialbd.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arial.ttf",
    ]
    for c in candidates:
        if c.exists():
            return str(c).replace("\\", "/")
    # 兜底
    return "arialbd.ttf"


def _run(cmd: list[str]) -> None:
    """运行 FFmpeg 命令，失败抛异常。"""
    print("[ffmpeg]>", " ".join(cmd[:6]), "...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ffmpeg STDERR]", res.stderr[-1500:])
        raise RuntimeError(f"FFmpeg 失败: {res.returncode}")


def _make_segment(img_path: str, effect: str, duration: float, fps: int,
                  tmp_dir: str, idx: int) -> str:
    """生成单段视频片段（含动感效果），输出 1080x1920 H.264。"""
    out = os.path.join(tmp_dir, f"seg_{idx:02d}.mp4")
    n_frames = max(1, int(duration * fps))
    W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT

    # zoompan 需要输入尺寸 > 输出以留出缩放余量
    base_scale = f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2}"

    if effect == "ken_burns":
        # 缓慢拉近 + 轻微平移
        zp = (
            f"zoompan=z='min(zoom+0.0012,1.4)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={n_frames}:s={W}x{H}:fps={fps}"
        )
    elif effect == "zoom_in":
        zp = (
            f"zoompan=z='min(zoom+0.0028,1.5)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)*0.8':"
            f"d={n_frames}:s={W}x{H}:fps={fps}"
        )
    elif effect == "flash":
        # 快闪：亮度脉冲 + 快速缩放（eq 用 t 时间变量，非 zoompan 的 on）
        zp = (
            f"zoompan=z='if(lte(on,3),1.2,min(zoom+0.004,1.35))':"
            f"d={n_frames}:s={W}x{H}:fps={fps},"
            f"eq=brightness='0.15*sin(t*18.8)':contrast=1.1:saturation=1.3"
        )
    elif effect == "slide":
        zp = (
            f"zoompan=z='min(zoom+0.0015,1.3)':"
            f"x='iw/2-(iw/zoom/2)+iw*0.1*on/{n_frames}':y='ih/2-(ih/zoom/2)':"
            f"d={n_frames}:s={W}x{H}:fps={fps}"
        )
    else:
        zp = f"zoompan=d={n_frames}:s={W}x{H}:fps={fps}"

    vf = f"{base_scale},{zp},setsar=1,format=yuv420p"
    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", img_path,
        "-t", str(duration), "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(fps),
        out,
    ]
    _run(cmd)
    return out


def _concat_segments(seg_paths: list[str], transition: str, out_path: str, fps: int) -> str:
    """拼接片段。片段≥2 时用 xfade 转场，否则直接复制。"""
    if len(seg_paths) == 1:
        shutil.copy2(seg_paths[0], out_path)
        return out_path

    # 用 concat demuxer 简单拼接（最稳定）
    list_file = out_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in seg_paths:
            f.write(f"file '{p.replace(chr(92), '/')}'\n")
    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", out_path,
    ]
    _run(cmd)
    try:
        os.remove(list_file)
    except OSError:
        pass
    return out_path


def _get_duration(path: str) -> float:
    cmd = [
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except ValueError:
        return 0.0


def _add_audio(video_path: str, template: Template, out_path: str) -> str:
    """为视频添加 BGM。无预置音轨则程序化生成。"""
    duration = _get_duration(video_path) or template.duration
    bgm_path = ""
    if template.bgm:
        candidate = config.BGM_DIR / template.bgm
        if candidate.exists():
            bgm_path = str(candidate)

    if not bgm_path:
        # 程序化生成
        bgm_path = os.path.join(config.BGM_DIR, f"_gen_{template.id}.wav")
        if not os.path.exists(bgm_path):
            bgm_gen.generate_bgm(bgm_path, duration + 0.5, bpm=120, seed=hash(template.id) % 1000)

    # 截取/循环 BGM 对齐视频时长
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-i", bgm_path,
        "-filter_complex",
        f"[1:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume=0.7[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", out_path,
    ]
    _run(cmd)
    return out_path


def _escape_drawtext(text: str) -> str:
    """转义 drawtext 文本中的特殊字符。"""
    for ch in (":", "\\", "'", "%"):
        text = text.replace(ch, "\\" + ch)
    return text


def _escape_font_path(path: str) -> str:
    """转义 fontfile 路径中的盘符冒号 (Windows: C:/ -> C\\:/)。

    FFmpeg 滤镜以 : 分隔键值，盘符冒号会破坏解析，需用反斜杠转义。
    """
    # 仅转义第一个冒号（盘符），路径其余部分保持正斜杠
    return path.replace(":/", "\\:/", 1) if ":/" in path else path


def _burn_hook(video_path: str, hook_text: str, hook_duration: float, out_path: str) -> str:
    """在视频前 hook_duration 秒烧录黄金 Hook 花字。"""
    if not hook_text:
        shutil.copy2(video_path, out_path)
        return out_path

    font = _escape_font_path(_font_path())
    W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT
    text = _escape_drawtext(hook_text)
    # 大字居中偏上，带描边，前 N 秒显示后淡出
    drawtext = (
        f"drawtext=fontfile='{font}':text='{text}':"
        f"fontcolor=white:fontsize=120:borderw=6:bordercolor=black@0.85:"
        f"x=(w-text_w)/2:y=h*0.32:"
        f"enable='between(t,0,{hook_duration:.2f})'"
    )
    cmd = [
        FFMPEG, "-y", "-i", video_path,
        "-vf", drawtext,
        "-c:a", "copy", "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        out_path,
    ]
    _run(cmd)
    return out_path


def make_thumbnail(video_path: str, out_path: str) -> str:
    """抽取视频第 1 秒作为缩略图。"""
    cmd = [
        FFMPEG, "-y", "-ss", "1", "-i", video_path,
        "-frames:v", "1", "-q:v", "2", out_path,
    ]
    _run(cmd)
    return out_path


def render(processed_images: list[str], template: Template, out_dir: str, note: str = "") -> tuple[str, str]:
    """主入口：合成最终视频。

    返回 (video_path, thumbnail_path)。
    """
    tmp_dir = os.path.join(out_dir, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    fps = 25

    # 若无处理图，生成占位黑底
    if not processed_images:
        placeholder = os.path.join(tmp_dir, "placeholder.jpg")
        _make_placeholder(placeholder)
        processed_images = [placeholder]

    # 1. 每段生成片段（图片数 < 片段数时循环复用，保证成片匹配模板时长）
    seg_paths: list[str] = []
    n_imgs = len(processed_images)
    n_segs = len(template.segments)
    for i, seg in enumerate(template.segments):
        img = processed_images[i % n_imgs] if n_imgs else processed_images[0]
        seg_paths.append(_make_segment(img, seg.effect, seg.duration, fps, tmp_dir, i))

    # 2. 拼接
    concat_path = os.path.join(tmp_dir, "concat.mp4")
    _concat_segments(seg_paths, template.transition, concat_path, fps)

    # 3. 加 BGM
    with_audio = os.path.join(tmp_dir, "with_audio.mp4")
    _add_audio(concat_path, template, with_audio)

    # 4. 烧录花字
    final_path = os.path.join(out_dir, "final.mp4")
    _burn_hook(with_audio, template.hook_text, template.hook_duration, final_path)

    # 5. 缩略图
    thumb_path = os.path.join(out_dir, "thumb.jpg")
    try:
        make_thumbnail(final_path, thumb_path)
    except Exception as e:
        print(f"[renderer] 缩略图失败: {e}")

    # 清理临时
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"[renderer] 渲染完成 -> {final_path}")
    return final_path, thumb_path


def _make_placeholder(path: str) -> None:
    """生成 1080x1920 占位图。"""
    import numpy as np
    import cv2
    img = np.zeros((config.OUTPUT_HEIGHT, config.OUTPUT_WIDTH, 3), dtype=np.uint8)
    cv2.putText(img, "No Image", (250, 960), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
    cv2.imwrite(path, img)
