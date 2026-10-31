"""EPIC 4 - Agent-based reasoning.

A transparent, rule-based reasoning agent. It observes fused engagement windows,
reasons over trends (drops, peaks, monologue, silence) and emits teaching
suggestions WITH its reasoning trace. It never makes decisions about students -
it is an assistive decision-support tool for the instructor.
"""
from typing import List

from .config import Config
from .models import Suggestion, Window

DISCLAIMER = ("Decision support only: suggestions are based on aggregate behavioural "
              "signals and should be weighed with the instructor's own judgement.")


def _fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


class TeachingAgent:
    def __init__(self, cfg: Config = None):
        self.cfg = cfg or Config()

    def run(self, windows: List[Window]) -> List[Suggestion]:
        c, out = self.cfg, []
        mono_run = 0
        for i, w in enumerate(windows):
            span = f"{_fmt(w.start)}-{_fmt(w.end)}"
            prev = windows[i - 1] if i else None

            # 1. attention drop
            if prev and prev.engagement - w.engagement >= c.drop_delta:
                out.append(Suggestion(
                    w.start, w.end, "attention",
                    f"Engagement fell from {prev.engagement:.2f} to {w.engagement:.2f} at {span}.",
                    "Pause and check understanding, or switch to a quick poll/question.",
                    min(0.5 + (prev.engagement - w.engagement), 0.95),
                    [f"drop of {prev.engagement - w.engagement:.2f} >= {c.drop_delta}",
                     f"attention={w.attention:.2f}, activity={w.activity:.2f}"]))
            elif w.engagement < c.low_engagement and w.participants > 0:
                out.append(Suggestion(
                    w.start, w.end, "attention",
                    f"Sustained low engagement ({w.engagement:.2f}) at {span}.",
                    "Introduce an interactive activity or a short break.",
                    0.65, [f"engagement {w.engagement:.2f} < {c.low_engagement}"]))

            # 2. teacher monologue -> pacing
            if w.speech_ratio is not None and w.speech_ratio >= c.monologue_speech_ratio:
                mono_run += 1
            else:
                mono_run = 0
            if mono_run == c.monologue_windows:
                out.append(Suggestion(
                    w.start, w.end, "pacing",
                    f"Near-continuous speech for {c.monologue_windows} consecutive windows ending {_fmt(w.end)}.",
                    "Slow the pace: insert pauses, examples, or a student-led question.",
                    0.8, [f"speech_ratio >= {c.monologue_speech_ratio} x{c.monologue_windows}"]))

            # 3. silence + inactivity -> classroom management
            if (w.speech_ratio is not None and w.speech_ratio <= c.silence_speech_ratio
                    and w.activity <= 0.15 and w.participants > 0):
                out.append(Suggestion(
                    w.start, w.end, "interaction",
                    f"Room was quiet and still at {span}.",
                    "If this is not planned work time, prompt discussion or group work.",
                    0.6, [f"speech_ratio={w.speech_ratio:.2f}", f"activity={w.activity:.2f}"]))

            # 4. peaks -> reinforce what worked
            is_peak = (w.engagement >= c.peak_engagement and
                       (not prev or w.engagement >= prev.engagement) and
                       (i == len(windows) - 1 or w.engagement >= windows[i + 1].engagement))
            if is_peak:
                out.append(Suggestion(
                    w.start, w.end, "positive",
                    f"Engagement peaked ({w.engagement:.2f}) at {span}.",
                    "Note what you were doing here (activity, topic, format) and repeat it.",
                    0.7, [f"engagement {w.engagement:.2f} >= {c.peak_engagement}, local maximum"]))
        return out
