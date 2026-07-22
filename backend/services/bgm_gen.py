"""程序化 BGM 生成：当模板缺少预置音轨时，合成一段简短悦耳的循环音乐。

用 numpy 合成和弦琶音 + 软 kick + hi-hat，导出 WAV。
让卡点视频在无版权音轨时仍有真实音乐。
"""
from __future__ import annotations
import math
import wave
import struct
import numpy as np


def _note_freq(n: int) -> float:
    """MIDI 音符号 → 频率。"""
    return 440.0 * (2 ** ((n - 69) / 12))


# 简单悦耳的和弦进行 (Cmaj - Gmaj - Amin - Fmaj) 的 MIDI 音
_CHORDS = [
    [60, 64, 67],   # C major
    [55, 59, 62],   # G major
    [57, 60, 64],   # A minor
    [53, 57, 60],   # F major
]


def generate_bgm(out_wav: str, duration: float, bpm: int = 120, seed: int = 0) -> str:
    """生成一段 BGM 并保存为 16-bit PCM WAV。"""
    sr = 44100
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    rng = np.random.default_rng(seed)
    audio = np.zeros(n_samples, dtype=np.float64)

    beat_dur = 60.0 / bpm
    chord_dur = beat_dur * 4  # 每和弦 4 拍

    # --- 和弦琶音 pad ---
    idx = 0
    pos = 0.0
    while pos < duration:
        chord = _CHORDS[idx % len(_CHORDS)]
        idx += 1
        seg_len = min(chord_dur, duration - pos)
        seg_n = int(sr * seg_len)
        seg_t = np.linspace(0, seg_len, seg_n, endpoint=False)
        for ni, note in enumerate(chord):
            f = _note_freq(note)
            # 琶音：每个音错开一点
            offset = int(sr * ni * beat_dur * 0.25)
            env = np.exp(-seg_t * 1.2)
            tone = np.sin(2 * np.pi * f * seg_t) * 0.08 * env
            end = min(offset + len(tone), n_samples)
            if offset < n_samples:
                audio[int(pos * sr) + offset:end] += tone[:end - offset - int(pos * sr) - offset + offset]
        pos += seg_len

    # 简化：直接逐拍加 pad
    audio = np.zeros(n_samples, dtype=np.float64)
    pos = 0.0
    idx = 0
    while pos < duration:
        chord = _CHORDS[idx % len(_CHORDS)]
        idx += 1
        seg_len = min(chord_dur, duration - pos)
        seg_n = int(sr * seg_len)
        for ni, note in enumerate(chord):
            f = _note_freq(note)
            seg_t = np.linspace(0, seg_len, seg_n, endpoint=False)
            env = np.exp(-seg_t * 0.8) * (1 - np.exp(-seg_t * 8))
            tone = np.sin(2 * np.pi * f * seg_t) * 0.06 * env
            start = int(pos * sr)
            end = min(start + seg_n, n_samples)
            audio[start:end] += tone[:end - start]
        pos += seg_len

    # --- kick drum (每拍) ---
    n_beats = int(duration / beat_dur)
    for b in range(n_beats):
        bp = b * beat_dur
        if bp >= duration:
            break
        start = int(bp * sr)
        kdur = 0.18
        kn = int(sr * kdur)
        kt = np.linspace(0, kdur, kn, endpoint=False)
        kick_freq = 60 * np.exp(-kt * 25) + 40
        kick = np.sin(2 * np.pi * kick_freq * kt) * np.exp(-kt * 9) * 0.5
        end = min(start + kn, n_samples)
        audio[start:end] += kick[:end - start]

    # --- hi-hat (反拍) ---
    for b in range(n_beats):
        for off in (0.5,):
            bp = b * beat_dur + beat_dur * off
            if bp >= duration:
                break
            start = int(bp * sr)
            hdur = 0.05
            hn = int(sr * hdur)
            noise = rng.standard_normal(hn) * np.exp(-np.linspace(0, hdur, hn) * 40) * 0.08
            end = min(start + hn, n_samples)
            audio[start:end] += noise[:end - start]

    # 归一化 + 淡入淡出
    peak = np.max(np.abs(audio)) or 1.0
    audio = audio / peak * 0.7
    fade = int(sr * 0.3)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    audio = np.clip(audio, -1, 1)

    # 写 WAV
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav
