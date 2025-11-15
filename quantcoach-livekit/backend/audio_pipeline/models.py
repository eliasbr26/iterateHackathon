"""
Data models for audio pipeline
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Transcript:
    """Represents a speech transcript with speaker information"""
    text: str
    speaker: str  # "recruiter" or "candidate"
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    is_final: bool = True

    def __repr__(self) -> str:
        duration = ""
        if self.start_ms is not None and self.end_ms is not None:
            duration = f" [{self.start_ms}ms - {self.end_ms}ms]"
        final_marker = "✓" if self.is_final else "~"
        return f"[{self.speaker}]{duration} {final_marker} {self.text}"
