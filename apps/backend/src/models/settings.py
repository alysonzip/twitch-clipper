from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Settings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)  # singleton
    obs_recordings_path: str = r"E:\OBS\Recordings"
    clips_output_path: str = r"E:\clips\prontos"
    temp_path: str = r"E:\clips\processando"
    twitch_client_id: Optional[str] = None
    twitch_client_secret_encrypted: Optional[str] = None
    twitch_access_token: Optional[str] = None
    twitch_refresh_token: Optional[str] = None
    gemini_api_key: Optional[str] = None
    whisper_model: str = "base"  # tiny, base, small
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    virality_threshold: float = 0.85
    min_clip_duration: int = 15
    max_clip_duration: int = 60
    live_buffer_minutes: int = 2
    live_segment_seconds: int = 30
    add_hook_titles: bool = True
    add_broll: bool = False
    subtitle_style: str = "karaoke"  # karaoke, pop, minimal
    auto_start: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)