"""Plain data containers shared across modules."""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


@dataclass
class FaceObs:
    t: float                       # seconds from start of session
    track_id: int
    box: Tuple[int, int, int, int]  # x, y, w, h
    facing: bool                   # True = frontal (attentive), False = profile/turned
    motion: float = 0.0            # normalised displacement per second


@dataclass
class AudioWindow:
    start: float
    end: float
    speech_ratio: float            # share of time with speech
    level_db: float                # mean level while speaking
    turns: int                     # speech onsets = interaction events


@dataclass
class Window:
    start: float
    end: float
    participants: float            # mean number of faces seen
    attention: float
    activity: float
    interaction: Optional[float]   # None if no audio supplied
    speech_ratio: Optional[float]
    engagement: float

    def to_dict(self):
        return asdict(self)


@dataclass
class Suggestion:
    start: float
    end: float
    category: str                  # pacing | interaction | attention | positive
    observation: str
    suggestion: str
    confidence: float
    reasoning: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
