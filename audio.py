"""EPIC 3 - Audio module.

Pure-NumPy signal processing: frame energy, adaptive voice-activity detection and
speech-turn counting. We only keep numeric features - raw audio is never stored
or transcribed, which keeps the system privacy-preserving.
"""
import shutil
import subprocess
import tempfile
import wave
from typing import List, Tuple

import numpy as np

from .config import Config
from .models import AudioWindow


def extract_audio(video_path: str) -> str:
    """Pull mono 16 kHz WAV from a video with ffmpeg (if installed). Returns wav path."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found; supply a .wav with --audio instead.")
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video_path,
                    "-vn", "-ac", "1", "-ar", "16000", out], check=True)
    return out


def load_wav(path: str) -> Tuple[np.ndarray, int]:
    with wave.open(path, "rb") as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise ValueError("Only 16-bit PCM WAV supported.")
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def frame_levels_db(x: np.ndarray, sr: int, frame_ms: int) -> np.ndarray:
    n = int(sr * frame_ms / 1000)
    count = len(x) // n
    if count == 0:
        return np.array([])
    frames = x[: count * n].reshape(count, n)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-9)


def detect_speech(levels_db: np.ndarray, margin_db: float) -> np.ndarray:
    """Adaptive VAD: speech = louder than (noise floor + margin), median-smoothed."""
    if len(levels_db) == 0:
        return np.array([], dtype=bool)
    floor = np.percentile(levels_db, 20)
    mask = levels_db > floor + margin_db
    k = 5   # smooth out single-frame flicker
    padded = np.pad(mask.astype(int), k // 2, mode="edge")
    return np.convolve(padded, np.ones(k), mode="valid") >= (k // 2 + 1)


def analyse_audio(path: str, cfg: Config = None) -> List[AudioWindow]:
    cfg = cfg or Config()
    x, sr = load_wav(path)
    levels = frame_levels_db(x, sr, cfg.audio_frame_ms)
    speech = detect_speech(levels, cfg.vad_margin_db)
    fps = 1000 / cfg.audio_frame_ms
    per = int(cfg.window_sec * fps)
    windows = []
    for s in range(0, len(speech), per):
        seg, lv = speech[s:s + per], levels[s:s + per]
        if len(seg) < per // 2:
            break
        onsets = int(((seg[1:] == 1) & (seg[:-1] == 0)).sum() + (1 if seg[0] else 0))
        windows.append(AudioWindow(
            start=s / fps, end=(s + len(seg)) / fps,
            speech_ratio=float(seg.mean()),
            level_db=float(lv[seg].mean()) if seg.any() else -90.0,
            turns=onsets))
    return windows
