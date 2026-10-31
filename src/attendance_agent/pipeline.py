"""EPIC 4/5/6 - end-to-end pipeline: video(+audio) -> logs, trends, suggestions, report."""
import os
from typing import Optional

from .agent import TeachingAgent
from .analytics import build_attendance, export, fuse, summarise
from .audio import analyse_audio, extract_audio
from .config import Config
from .report import write_report
from .simulate import simulate_session
from .vision import VisionAnalyzer


def _finish(obs, audio, duration, out_dir, cfg, title):
    attendance = build_attendance(obs, cfg)
    windows = fuse(obs, audio, duration, cfg)
    suggestions = TeachingAgent(cfg).run(windows)
    summary = summarise(windows, attendance)
    export(out_dir, attendance, windows, suggestions, summary)
    write_report(os.path.join(out_dir, "report.html"), title, summary, attendance, windows, suggestions)
    return {"attendance": attendance, "windows": windows,
            "suggestions": suggestions, "summary": summary}


def analyse(video: str, out_dir: str, audio_path: Optional[str] = None,
            cfg: Config = None, progress=None):
    cfg = cfg or Config()
    obs, duration = VisionAnalyzer(cfg).process_video(video, progress)
    audio = None
    try:
        audio = analyse_audio(audio_path or extract_audio(video), cfg)
    except Exception as exc:                     # vision-only fallback
        print(f"[info] audio skipped: {exc}")
    return _finish(obs, audio, duration, out_dir, cfg, "Multimodal Attendance & Engagement Report")


def demo(out_dir: str, cfg: Config = None):
    cfg = cfg or Config()
    obs, audio, duration = simulate_session(cfg=cfg)
    return _finish(obs, audio, duration, out_dir, cfg, "Demo Session - Engagement Report")
