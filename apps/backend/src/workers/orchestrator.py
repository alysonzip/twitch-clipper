import yt_dlp
import ffmpeg
from pathlib import Path
from typing import List, Optional

from arq import ArqRedis
from arq.connections import RedisSettings

from src.models.job import Job
from src.models.clip import Clip
from src.models.settings import Settings
from src.database import engine, get_session
from sqlmodel import Session, select
from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.schemas.gemini import ViralAnalysisResult, ViralClip
from src.schemas.render import RenderOptions
from src.workers.whisper_worker import WhisperWorker
from src.workers.gemini_worker import GeminiWorker
from src.workers.render_worker import FFmpegRenderer
from src.services.settings_service import SettingsService


async def process_vod_job(ctx, job_id: int):
    """Full pipeline: download VOD -> transcribe -> analyze viral -> render clips."""
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return

        settings = session.get(Settings, 1)
        job.status = "processing"
        job.current_step = "downloading"
        job.progress = 5
        session.add(job)
        session.commit()

        try:
            # Step 1: Download VOD
            job.current_step = "downloading"
            job.progress = 10
            session.add(job)
            session.commit()

            vod_path = await download_vod(job.source_url, settings.temp_path)
            job.source_path = vod_path
            session.add(job)
            session.commit()

            # Step 2: Transcribe
            job.current_step = "transcribing"
            job.progress = 25
            session.add(job)
            session.commit()

            whisper_worker = WhisperWorker(session)
            transcription = whisper_worker.transcribe_audio(vod_path)

            # Store transcription for next steps
            transcription_data = transcription.model_dump()

            # Step 3: Analyze viral
            job.current_step = "analyzing"
            job.progress = 55
            session.add(job)
            session.commit()

            gemini_worker = GeminiWorker(session)
            viral_result = gemini_worker.analyze_viral(transcription)

            if not viral_result.clips:
                job.status = "done"
                job.progress = 100
                job.current_step = "completed - no viral clips found"
                session.add(job)
                session.commit()
                return

            # Step 4: Create Clip records
            clip_ids = []
            for i, viral_clip in enumerate(viral_result.clips):
                clip = Clip(
                    source_path=vod_path,
                    source_type="vod",
                    start=viral_clip.start,
                    end=viral_clip.end,
                    duration=viral_clip.end - viral_clip.start,
                    score=viral_clip.score,
                    reason=viral_clip.reason,
                    output_path=str(Path(settings.clips_output_path) / f"vod_{job_id}_clip_{i}.mp4"),
                    status="pending",
                )
                session.add(clip)
                session.commit()
                session.refresh(clip)
                clip_ids.append(clip.id)

            job.result_clips = clip_ids
            session.add(job)
            session.commit()

            # Step 5: Render clips
            job.current_step = "rendering"
            job.progress = 75
            session.add(job)
            session.commit()

            renderer = FFmpegRenderer(session)
            render_options = RenderOptions(
                subtitle_style=settings.subtitle_style,
                add_hook_titles=settings.add_hook_titles,
            )

            for clip_id in clip_ids:
                clip = session.get(Clip, clip_id)
                clip.status = "processing"
                session.add(clip)

                # Find corresponding viral clip
                viral_clip = next(vc for vc in viral_result.clips if vc.start == clip.start and vc.end == clip.end)

                result = renderer.render_clip(
                    source_path=vod_path,
                    clip=viral_clip,
                    transcription=transcription,
                    output_path=clip.output_path,
                    options=render_options,
                )

                clip.status = "done"
                clip.output_path = result.output_path
                session.add(clip)

            job.status = "done"
            job.progress = 100
            job.current_step = "completed"
            session.add(job)
            session.commit()

        except Exception as e:
            job.status = "failed"
            job.error = f"VOD processing failed: {str(e)}"
            session.add(job)
            session.commit()
            raise


async def process_live_segment_job(ctx, job_id: int, video_path: str, start_offset: float = 0):
    """Process live segment: transcribe last N minutes -> analyze -> render."""
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return

        settings = session.get(Settings, 1)
        job.status = "processing"
        job.current_step = "transcribing"
        job.progress = 20
        session.add(job)
        session.commit()

        try:
            # Step 1: Extract segment (last N seconds from video)
            segment_path = await extract_live_segment(video_path, start_offset, settings.live_segment_seconds, settings.temp_path)
            job.source_path = segment_path
            session.add(job)
            session.commit()

            # Step 2: Transcribe segment
            job.current_step = "transcribing"
            job.progress = 40
            session.add(job)
            session.commit()

            whisper_worker = WhisperWorker(session)
            transcription = whisper_worker.transcribe_audio(segment_path)

            # Step 3: Analyze viral
            job.current_step = "analyzing"
            job.progress = 60
            session.add(job)
            session.commit()

            gemini_worker = GeminiWorker(session)
            viral_result = gemini_worker.analyze_viral(transcription)

            if not viral_result.clips:
                job.status = "done"
                job.progress = 100
                job.current_step = "completed - no viral clips in segment"
                session.add(job)
                session.commit()
                return

            # Step 4: Create Clip records
            clip_ids = []
            for i, viral_clip in enumerate(viral_result.clips):
                clip = Clip(
                    source_path=segment_path,
                    source_type="live",
                    start=viral_clip.start + start_offset,
                    end=viral_clip.end + start_offset,
                    duration=viral_clip.end - viral_clip.start,
                    score=viral_clip.score,
                    reason=viral_clip.reason,
                    output_path=str(Path(settings.clips_output_path) / f"live_{job_id}_clip_{i}.mp4"),
                    status="pending",
                )
                session.add(clip)
                session.commit()
                session.refresh(clip)
                clip_ids.append(clip.id)

            job.result_clips = clip_ids
            session.add(job)
            session.commit()

            # Step 5: Render clips
            job.current_step = "rendering"
            job.progress = 80
            session.add(job)
            session.commit()

            renderer = FFmpegRenderer(session)
            render_options = RenderOptions(
                subtitle_style=settings.subtitle_style,
                add_hook_titles=settings.add_hook_titles,
            )

            for clip_id in clip_ids:
                clip = session.get(Clip, clip_id)
                clip.status = "processing"
                session.add(clip)

                viral_clip = next(vc for vc in viral_result.clips if vc.start == clip.start - start_offset and vc.end == clip.end - start_offset)

                result = renderer.render_clip(
                    source_path=segment_path,
                    clip=viral_clip,
                    transcription=transcription,
                    output_path=clip.output_path,
                    options=render_options,
                )

                clip.status = "done"
                clip.output_path = result.output_path
                session.add(clip)

            job.status = "done"
            job.progress = 100
            job.current_step = "completed"
            session.add(job)
            session.commit()

        except Exception as e:
            job.status = "failed"
            job.error = f"Live segment processing failed: {str(e)}"
            session.add(job)
            session.commit()
            raise


async def download_vod(url: str, output_dir: str) -> str:
    """Download VOD using yt-dlp."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract VOD ID from URL for filename
    import re
    vod_id = re.search(r'(?:videos?/|v/)(\d+)', url)
    vod_id = vod_id.group(1) if vod_id else "vod"

    output_file = output_path / f"{vod_id}.mp4"

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': str(output_file),
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return str(output_file)


async def extract_live_segment(source_path: str, start_offset: float, duration: int, output_dir: str) -> str:
    """Extract last N seconds from live recording using ffmpeg."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f"live_segment_{int(start_offset)}_{duration}.mp4"

    # Get video duration
    probe = ffmpeg.probe(source_path)
    video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    total_duration = float(video_stream['duration'])

    # Calculate start time (from end minus offset minus duration)
    segment_start = max(0, total_duration - start_offset - duration)

    stream = ffmpeg.input(source_path, ss=segment_start, t=duration)
    stream = stream.output(str(output_file), c='copy')
    stream = stream.overwrite_output()
    stream.run(capture_stdout=True, capture_stderr=True)

    return str(output_file)


# ARQ Worker Settings
class WorkerSettings:
    functions = [
        process_vod_job,
        process_live_segment_job,
    ]
    redis_settings = RedisSettings(
        host="localhost",
        port=6379,
        database=0,
    )
    cron_jobs = []
    max_jobs = 2  # Limit concurrent jobs
    job_timeout = 1800  # 30 minutes max per job
    keep_result = 86400  # Keep results for 24 hours