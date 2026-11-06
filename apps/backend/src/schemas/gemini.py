from pydantic import BaseModel
from typing import List


class ViralClip(BaseModel):
    start: float
    end: float
    score: float
    reason: str
    hook_title: str


class ViralAnalysisResult(BaseModel):
    clips: List[ViralClip]
    full_transcript: str