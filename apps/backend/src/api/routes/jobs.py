from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlmodel import Session, select
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

from src.database import get_session
from src.models.job import Job
from src.models.clip import Clip

router = APIRouter()


class CreateJobRequest(BaseModel):
    type: str  # "vod" | "live"
    source_url: Optional[HttpUrl] = None
    source_path: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    type: str
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    status: str
    progress: int
    current_step: str
    result_clips: list[int]
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@router.get("")
async def list_jobs(
    session: Session = Depends(get_session),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    query = select(Job).order_by(Job.created_at.desc())
    if status:
        query = query.where(Job.status == status)
    jobs = session.exec(query.offset(offset).limit(limit)).all()
    return {"jobs": jobs, "total": len(jobs)}


@router.post("")
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    job = Job(
        type=request.type,
        source_url=str(request.source_url) if request.source_url else None,
        source_path=request.source_path,
        status="queued",
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # In real implementation, this would enqueue to ARQ
    # background_tasks.add_task(process_job, job.id)

    return JobResponse.model_validate(job)


@router.get("/{job_id}")
async def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["done", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job.status = "failed"
    job.error = "Cancelled by user"
    job.completed_at = datetime.utcnow()
    session.add(job)
    session.commit()
    return {"message": "Job cancelled"}


@router.post("/{job_id}/retry")
async def retry_job(job_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Reset job for retry
    job.status = "queued"
    job.progress = 0
    job.current_step = ""
    job.error = None
    job.started_at = None
    job.completed_at = None
    session.add(job)
    session.commit()

    # Re-enqueue
    # background_tasks.add_task(process_job, job.id)

    return {"message": "Job re-queued"}