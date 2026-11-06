from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlmodel import Session, select
from typing import Optional
from pathlib import Path

from src.database import get_session
from src.models.clip import Clip

router = APIRouter()


@router.get("")
async def list_clips(
    session: Session = Depends(get_session),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    query = select(Clip).order_by(Clip.created_at.desc())
    if status:
        query = query.where(Clip.status == status)
    clips = session.exec(query.offset(offset).limit(limit)).all()
    return {"clips": clips, "total": len(clips)}


@router.get("/{clip_id}")
async def get_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.get("/{clip_id}/play")
async def play_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip or not clip.output_path:
        raise HTTPException(status_code=404, detail="Clip not found or not ready")

    path = Path(clip.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip file not found")

    # Return file for streaming
    from fastapi.responses import FileResponse
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.delete("/{clip_id}")
async def delete_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Delete file if exists
    if clip.output_path:
        path = Path(clip.output_path)
        if path.exists():
            path.unlink()

    session.delete(clip)
    session.commit()
    return {"message": "Clip deleted"}