from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_path: str
    source_type: str  # "vod" | "live"
    start: float
    end: float
    duration: float
    score: float
    reason: str
    output_path: Optional[str] = None
    status: str = "pending"  # pending, processing, done, failed
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None