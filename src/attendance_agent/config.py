"""EPIC 1 - central configuration. Everything runs offline; nothing leaves the machine."""
from dataclasses import dataclass, field


@dataclass
class Config:
    # ---- Vision ----
    sample_fps: float = 2.0            # frames analysed per second of video
    min_face_px: int = 40              # ignore tiny detections
    max_missing_sec: float = 4.0       # tracker forgives short occlusions
    match_dist_ratio: float = 0.12     # max centroid jump (fraction of frame width)

    # ---- Attendance ----
    # A participant counts as present only after SUSTAINED presence, which
    # filters out one-frame false positives and people walking past.
    min_presence_sec: float = 10.0
    present_ratio_threshold: float = 0.60   # present if seen >=60% of their span

    # ---- Audio ----
    audio_frame_ms: int = 30
    vad_margin_db: float = 8.0         # speech = noise floor + margin

    # ---- Fusion / analytics ----
    window_sec: int = 30
    weights: dict = field(default_factory=lambda: {
        "attention": 0.50,     # facing the front / camera
        "activity": 0.20,      # healthy amount of movement
        "interaction": 0.30,   # conversation turns in audio
    })
    target_motion: float = 0.35        # normalised motion considered "active"
    target_turns_per_window: float = 4.0
    inactivity_motion: float = 0.03    # below this = inactive

    # ---- Agent thresholds ----
    low_engagement: float = 0.40
    peak_engagement: float = 0.72
    drop_delta: float = 0.20
    monologue_speech_ratio: float = 0.85
    monologue_windows: int = 3
    silence_speech_ratio: float = 0.08
