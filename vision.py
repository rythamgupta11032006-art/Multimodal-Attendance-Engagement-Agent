"""EPIC 2 - Vision module.

Offline face detection with OpenCV's bundled Haar cascades (no model download,
no cloud). Frontal face = attentive; profile face = turned away. A centroid
tracker gives each person an anonymous ID so we can compute sustained presence
and movement without ever storing identities or images.
"""
from typing import Dict, List, Tuple

import cv2
import numpy as np

from .config import Config
from .models import FaceObs

Box = Tuple[int, int, int, int]


def _iou(a: Box, b: Box) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


class CentroidTracker:
    """Greedy nearest-centroid tracker with a short memory for occlusions."""

    def __init__(self, max_dist_px: float, max_missing_sec: float):
        self.max_dist = max_dist_px
        self.max_missing = max_missing_sec
        self.next_id = 1
        self.tracks: Dict[int, dict] = {}

    def update(self, boxes: List[Box], t: float) -> List[Tuple[int, Box, float]]:
        """Returns [(track_id, box, motion_px_per_sec)]."""
        centroids = [(x + w / 2, y + h / 2) for x, y, w, h in boxes]
        # expire stale tracks
        for tid in [k for k, v in self.tracks.items() if t - v["t"] > self.max_missing]:
            del self.tracks[tid]

        pairs = []
        for tid, tr in self.tracks.items():
            for j, c in enumerate(centroids):
                d = float(np.hypot(c[0] - tr["c"][0], c[1] - tr["c"][1]))
                if d <= self.max_dist:
                    pairs.append((d, tid, j))
        pairs.sort()

        used_t, used_d, out = set(), set(), []
        for d, tid, j in pairs:
            if tid in used_t or j in used_d:
                continue
            used_t.add(tid)
            used_d.add(j)
            dt = max(t - self.tracks[tid]["t"], 1e-6)
            self.tracks[tid].update(c=centroids[j], t=t)
            out.append((tid, boxes[j], d / dt))
        for j, c in enumerate(centroids):
            if j in used_d:
                continue
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = {"c": c, "t": t}
            out.append((tid, boxes[j], 0.0))
        return out


class VisionAnalyzer:
    def __init__(self, cfg: Config = None):
        self.cfg = cfg or Config()
        base = cv2.data.haarcascades
        self.frontal = cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml")
        self.profile = cv2.CascadeClassifier(base + "haarcascade_profileface.xml")
        if self.frontal.empty() or self.profile.empty():
            raise RuntimeError("OpenCV Haar cascades not found - reinstall opencv-python.")

    def detect(self, frame) -> List[Tuple[Box, bool]]:
        """Return [(box, facing)] for one frame."""
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        mn = (self.cfg.min_face_px, self.cfg.min_face_px)
        found: List[Tuple[Box, bool]] = [
            (tuple(int(v) for v in b), True)
            for b in self.frontal.detectMultiScale(gray, 1.1, 5, minSize=mn)
        ]
        W = gray.shape[1]
        profiles = [tuple(int(v) for v in b) for b in self.profile.detectMultiScale(gray, 1.1, 5, minSize=mn)]
        for b in self.profile.detectMultiScale(cv2.flip(gray, 1), 1.1, 5, minSize=mn):
            x, y, w, h = (int(v) for v in b)
            profiles.append((W - x - w, y, w, h))   # un-flip
        for b in profiles:
            if all(_iou(b, f[0]) < 0.3 for f in found):
                found.append((b, False))
        return found

    def process_video(self, path: str, progress=None) -> Tuple[List[FaceObs], float]:
        """Analyse a video (or webcam index). Returns (observations, duration_sec)."""
        cap = cv2.VideoCapture(path if not str(path).isdigit() else int(path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        step = max(int(round(fps / self.cfg.sample_fps)), 1)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640
        tracker = CentroidTracker(width * self.cfg.match_dist_ratio, self.cfg.max_missing_sec)

        obs: List[FaceObs] = []
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                t = idx / fps
                dets = self.detect(frame)
                boxes = [d[0] for d in dets]
                facing = {b: f for b, f in dets}
                for tid, box, speed in tracker.update(boxes, t):
                    norm_motion = speed / max(box[2], 1)    # face-widths per second
                    obs.append(FaceObs(t, tid, box, facing[box], float(norm_motion)))
                if progress and total:
                    progress(idx / total)
            idx += 1
        cap.release()
        return obs, idx / fps
