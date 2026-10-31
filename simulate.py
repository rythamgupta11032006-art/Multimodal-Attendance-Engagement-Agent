"""Synthetic session generator - lets you demo and test with no camera/video."""
import random
from typing import List, Tuple

from .config import Config
from .models import AudioWindow, FaceObs


def simulate_session(minutes: int = 10, students: int = 6, seed: int = 7,
                     cfg: Config = None) -> Tuple[List[FaceObs], List[AudioWindow], float]:
    cfg = cfg or Config()
    rnd = random.Random(seed)
    duration = minutes * 60.0
    step = 1 / cfg.sample_fps
    obs: List[FaceObs] = []
    # engagement profile: warm-up, a monologue dip, an interactive peak, a tired ending
    def attn(t):
        m = t / 60
        return 0.75 if m < 3 else 0.35 if m < 5 else 0.9 if m < 7 else 0.5
    t = 0.0
    while t < duration:
        for sid in range(1, students + 1):
            if sid == students and t < 60:          # late joiner
                continue
            if rnd.random() < 0.06:                 # occasional missed detection
                continue
            obs.append(FaceObs(round(t, 3), sid, (100 * sid, 100, 80, 80),
                               rnd.random() < attn(t), abs(rnd.gauss(0.25, 0.1))))
        t += step
    audio: List[AudioWindow] = []
    for i in range(int(duration // cfg.window_sec)):
        m = i * cfg.window_sec / 60
        if 3 <= m < 5.5:      # lecturer monologue
            audio.append(AudioWindow(i * 30, i * 30 + 30, 0.93, -22, 1))
        elif 5.5 <= m < 7.5:  # discussion
            audio.append(AudioWindow(i * 30, i * 30 + 30, 0.55, -24, 7))
        else:
            audio.append(AudioWindow(i * 30, i * 30 + 30, 0.4, -26, 3))
    return obs, audio, duration
