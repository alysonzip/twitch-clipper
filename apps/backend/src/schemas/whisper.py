from pydantic import BaseModel
from typing import List, Optional


class Word(BaseModel):
    start: float
    end: float
    word: str
    probability: float


class Segment(BaseModel):
    start: float
    end: float
    text: str
    words: List[Word]


class TranscriptionResult(BaseModel):
    segments: List[Segment]
    language: str
    duration: float
    text: str