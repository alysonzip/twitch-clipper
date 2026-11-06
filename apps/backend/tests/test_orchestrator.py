import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.workers.orchestrator import (
    process_vod_job, process_live_segment_job,
    download_vod, extract_live_segment, WorkerSettings
)
from src.models.job import Job
from src.models.clip import Clip
from src.models.settings import Settings
from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.schemas.gemini import ViralAnalysisResult, ViralClip
from src.schemas.render import RenderResult
from src.database import engine, init_db, get_session


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    with next(get_session()) as session:
        session.exec(select(Job)).delete()
        session.exec(select(Clip)).delete()
        session.exec(select(Settings)).delete()
        session.commit()


@pytest.mark.asyncio
async def test_process_vod_job_full_pipeline():
    """Test VOD job runs full pipeline and creates clips."""
    with patch("src.workers.orchestrator.download_vod", new_callable=AsyncMock) as mock_download, \
         patch("src.workers.orchestrator.WhisperWorker") as mock_whisper, \
         patch("src.workers.orchestrator.GeminiWorker") as mock_gemini, \
         patch("src.workers.orchestrator.FFmpegRenderer") as mock_renderer:

        # Setup mocks
        mock_download.return_value = "/tmp/vod.mp4"

        mock_whisper_instance = MagicMock()
        mock_whisper.return_value = mock_whisper_instance
        mock_whisper_instance.transcribe_audio.return_value = TranscriptionResult(
            segments=[Segment(start=0.0, end=30.0, text="Test", words=[])],
            language="pt", duration=30.0, text="Test"
        )

        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance
        mock_gemini_instance.analyze_viral.return_value = ViralAnalysisResult(
            clips=[
                ViralClip(start=5.0, end=25.0, score=0.9, reason="Funny", hook_title="Hook 1"),
            ],
            full_transcript="Test"
        )

        mock_renderer_instance = MagicMock()
        mock_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_clip.return_value = RenderResult(
            output_path="/tmp/clip.mp4", duration=20.0, width=1080, height=1920
        )

        with next(get_session()) as session:
            settings = Settings()
            settings.clips_output_path = "/tmp/clips"
            settings.temp_path = "/tmp"
            settings.subtitle_style = "karaoke"
            settings.add_hook_titles = True
            session.add(settings)
            session.commit()

            job = Job(type="vod", source_url="https://twitch.tv/videos/123")
            session.add(job)
            session.commit()
            session.refresh(job)

        await process_vod_job(None, job.id)

        with next(get_session()) as session:
            job = session.get(Job, job.id)
            assert job.status == "done"
            assert job.progress == 100
            assert len(job.result_clips) == 1

            clip = session.get(Clip, job.result_clips[0])
            assert clip.status == "done"
            assert clip.output_path == "/tmp/clip.mp4"
            assert clip.score == 0.9


@pytest.mark.asyncio
async def test_process_vod_job_no_viral_clips():
    """Test VOD job completes when no viral clips found."""
    with patch("src.workers.orchestrator.download_vod", new_callable=AsyncMock) as mock_download, \
         patch("src.workers.orchestrator.WhisperWorker") as mock_whisper, \
         patch("src.workers.orchestrator.GeminiWorker") as mock_gemini:

        mock_download.return_value = "/tmp/vod.mp4"

        mock_whisper_instance = MagicMock()
        mock_whisper.return_value = mock_whisper_instance
        mock_whisper_instance.transcribe_audio.return_value = TranscriptionResult(
            segments=[Segment(start=0.0, end=30.0, text="Boring", words=[])],
            language="pt", duration=30.0, text="Boring"
        )

        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance
        mock_gemini_instance.analyze_viral.return_value = ViralAnalysisResult(
            clips=[], full_transcript="Boring"
        )

        with next(get_session()) as session:
            settings = Settings()
            session.add(settings)
            session.commit()

            job = Job(type="vod", source_url="https://twitch.tv/videos/123")
            session.add(job)
            session.commit()
            session.refresh(job)

        await process_vod_job(None, job.id)

        with next(get_session()) as session:
            job = session.get(Job, job.id)
            assert job.status == "done"
            assert "no viral clips" in job.current_step.lower()
            assert job.result_clips == []


@pytest.mark.asyncio
async def test_process_live_segment_job():
    """Test live segment job processes and creates clips."""
    with patch("src.workers.orchestrator.extract_live_segment", new_callable=AsyncMock) as mock_extract, \
         patch("src.workers.orchestrator.WhisperWorker") as mock_whisper, \
         patch("src.workers.orchestrator.GeminiWorker") as mock_gemini, \
         patch("src.workers.orchestrator.FFmpegRenderer") as mock_renderer:

        mock_extract.return_value = "/tmp/live_segment.mp4"

        mock_whisper_instance = MagicMock()
        mock_whisper.return_value = mock_whisper_instance
        mock_whisper_instance.transcribe_audio.return_value = TranscriptionResult(
            segments=[Segment(start=0.0, end=30.0, text="Live test", words=[])],
            language="pt", duration=30.0, text="Live test"
        )

        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance
        mock_gemini_instance.analyze_viral.return_value = ViralAnalysisResult(
            clips=[ViralClip(start=5.0, end=25.0, score=0.88, reason="Live clip", hook_title="Live Hook")],
            full_transcript="Live test"
        )

        mock_renderer_instance = MagicMock()
        mock_renderer.return_value = mock_renderer_instance
        mock_renderer_instance.render_clip.return_value = RenderResult(
            output_path="/tmp/live_clip.mp4", duration=20.0, width=1080, height=1920
        )

        with next(get_session()) as session:
            settings = Settings()
            settings.clips_output_path = "/tmp/clips"
            settings.temp_path = "/tmp"
            settings.live_segment_seconds = 30
            settings.subtitle_style = "karaoke"
            settings.add_hook_titles = True
            session.add(settings)
            session.commit()

            job = Job(type="live_segment", source_path="/tmp/live_recording.mp4")
            session.add(job)
            session.commit()
            session.refresh(job)

        await process_live_segment_job(None, job.id, "/tmp/live_recording.mp4", 0)

        with next(get_session()) as session:
            job = session.get(Job, job.id)
            assert job.status == "done"
            assert len(job.result_clips) == 1


def test_worker_settings_configuration():
    """Test ARQ WorkerSettings has correct configuration."""
    assert WorkerSettings.functions == [
        "process_vod_job",
        "process_live_segment_job",
    ]
    assert WorkerSettings.redis_settings.host == "localhost"
    assert WorkerSettings.redis_settings.port == 6379
    assert WorkerSettings.max_jobs == 2
    assert WorkerSettings.job_timeout == 1800


def test_download_vod_calls_ytdlp():
    """Test download_vod uses yt-dlp with correct options."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        import asyncio
        result = asyncio.run(download_vod("https://twitch.tv/videos/123", "/tmp"))

        assert "123.mp4" in result
        mock_ydl.download.assert_called_once_with(["https://twitch.tv/videos/123"])


def test_extract_live_segment_uses_ffmpeg():
    """Test extract_live_segment uses ffmpeg to extract segment."""
    with patch("src.workers.orchestrator.ffmpeg") as mock_ffmpeg:
        mock_probe = {
            'streams': [{'codec_type': 'video', 'duration': '100.0'}]
        }
        mock_ffmpeg.probe.return_value = mock_probe

        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.return_value = None

        import asyncio
        result = asyncio.run(extract_live_segment("/tmp/source.mp4", 10, 30, "/tmp"))

        assert "live_segment" in result
        mock_ffmpeg.input.assert_called()