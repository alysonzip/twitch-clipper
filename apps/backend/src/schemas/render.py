from pydantic import BaseModel
from typing import Optional


class RenderOptions(BaseModel):
    target_width: int = 1080
    target_height: int = 1920
    fps: int = 30
    subtitle_style: str = "karaoke"  # karaoke, pop, minimal
    add_hook_title: bool = True
    font_path: Optional[str] = None
    use_nvenc: bool = True


class RenderResult(BaseModel):
    output_path: str
    duration: float
    width: int
    height: int