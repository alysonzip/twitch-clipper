from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # "vod" | "live_segment"
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    status: str = "queued"  # queued, processing, done, failed
    progress: int = 0
    current_step: str = ""
    result_clips: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None