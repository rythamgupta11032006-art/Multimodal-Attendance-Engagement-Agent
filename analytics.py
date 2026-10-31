"""EPIC 5 (part 1) - attendance logs, multimodal fusion and engagement trends."""
import csv
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional

from .config import Config
from .models import AudioWindow, FaceObs, Window


# ---------------------------------------------------------------- attendance
def build_attendance(obs: List[FaceObs], cfg: Config = None) -> List[dict]:
    """Attendance from SUSTAINED presence, not single-frame detection."""
    cfg = cfg or Config()
    by_track: Dict[int, List[FaceObs]] = defaultdict(list)
    for o in obs:
        by_track[o.track_id].append(o)

    step = 1.0 / cfg.sample_fps
    rows = []
    for tid, items in sorted(by_track.items()):
        items.sort(key=lambda o: o.t)
        first, last = items[0].t, items[-1].t
        span = last - first + step
        seen = len(items) * step
        ratio = min(seen / span, 1.0)
        present = seen >= cfg.min_presence_sec and ratio >= cfg.present_ratio_threshold
        rows.append({
            "participant": f"Participant {tid}",
            "first_seen_s": round(first, 1),
            "last_seen_s": round(last, 1),
            "seen_seconds": round(seen, 1),
            "presence_ratio": round(ratio, 2),
            "status": "Present" if present else "Not confirmed",
        })
    return rows


# -------------------------------------------------------------------- fusion
def fuse(obs: List[FaceObs], audio: Optional[List[AudioWindow]], duration: float,
         cfg: Config = None) -> List[Window]:
    cfg = cfg or Config()
    w = cfg.weights
    windows: List[Window] = []
    n = max(int(duration // cfg.window_sec), 1)
    audio_by_idx = {int(a.start // cfg.window_sec): a for a in (audio or [])}

    for i in range(n):
        s, e = i * cfg.window_sec, min((i + 1) * cfg.window_sec, duration or cfg.window_sec)
        seg = [o for o in obs if s <= o.t < e]
        frames = {round(o.t, 3) for o in seg}
        participants = len(seg) / len(frames) if frames else 0.0
        attention = sum(o.facing for o in seg) / len(seg) if seg else 0.0
        motion = sum(o.motion for o in seg) / len(seg) if seg else 0.0
        activity = min(motion / cfg.target_motion, 1.0)

        a = audio_by_idx.get(i)
        interaction = speech_ratio = None
        score = w["attention"] * attention + w["activity"] * activity
        total_w = w["attention"] + w["activity"]
        if a is not None:
            interaction = min(a.turns / cfg.target_turns_per_window, 1.0)
            speech_ratio = a.speech_ratio
            score += w["interaction"] * interaction
            total_w += w["interaction"]
        windows.append(Window(s, e, round(participants, 2), round(attention, 3),
                              round(activity, 3),
                              None if interaction is None else round(interaction, 3),
                              None if speech_ratio is None else round(speech_ratio, 3),
                              round(score / total_w, 3)))
    return windows


def summarise(windows: List[Window], attendance: List[dict]) -> dict:
    if not windows:
        return {}
    eng = [w.engagement for w in windows]
    best = max(windows, key=lambda w: w.engagement)
    worst = min(windows, key=lambda w: w.engagement)
    return {
        "participants_present": sum(r["status"] == "Present" for r in attendance),
        "participants_detected": len(attendance),
        "mean_engagement": round(sum(eng) / len(eng), 3),
        "peak_window": [best.start, best.end, best.engagement],
        "lowest_window": [worst.start, worst.end, worst.engagement],
    }


# -------------------------------------------------------------------- export
def export(out_dir: str, attendance, windows, suggestions, summary):
    os.makedirs(out_dir, exist_ok=True)
    if attendance:
        with open(os.path.join(out_dir, "attendance_log.csv"), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(attendance[0].keys()))
            wr.writeheader()
            wr.writerows(attendance)
    with open(os.path.join(out_dir, "engagement_trends.json"), "w") as f:
        json.dump([w.to_dict() for w in windows], f, indent=2)
    with open(os.path.join(out_dir, "teaching_suggestions.json"), "w") as f:
        json.dump([s.to_dict() for s in suggestions], f, indent=2)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
