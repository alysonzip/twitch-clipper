"""
Integration tests for the full Twitch Clipper pipeline.
These tests require a running backend and Redis.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.workers.orchestrator import process_vod_job, process_live_segment_job
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_vod_pipeline_creates_clips():
    """Test complete VOD pipeline: download -> transcribe -> analyze -> render."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        clips_dir = tmpdir / "clips"
        clips_dir.mkdir()

        with patch("src.workers.orchestrator.download_vod", new_callable=AsyncMock) as mock_download, \
             patch("src.workers.orchestrator.WhisperWorker") as mock_whisper, \
             patch("src.workers.orchestrator.GeminiWorker") as mock_gemini, \
             patch("src.workers.orchestrator.FFmpegRenderer") as mock_renderer:

            # Setup mocks
            vod_path = tmpdir / "vod.mp4"
            vod_path.write_bytes(b"fake video content")
            mock_download.return_value = str(vod_path)

            mock_whisper_instance = MagicMock()
            mock_whisper.return_value = mock_whisper_instance
            mock_whisper_instance.transcribe_audio.return_value = TranscriptionResult(
                segments=[
                    Segment(start=0.0, end=5.0, text="Olá pessoal", words=[
                        Word(start=0.0, end=0.5, word="Olá", probability=0.99),
                        Word(start=0.6, end=1.2, word="pessoal", probability=0.98),
                    ]),
                    Segment(start=10.0, end=30.0, text="Nossa! Que fail incrível!", words=[
                        Word(start=10.0, end=10.5, word="Nossa", probability=0.99),
                        Word(start=10.6, end=11.2, word="fail", probability=0.97),
                        Word(start=11.3, end=12.0, word="incrível", probability=0.95),
                    ]),
                ],
                language="pt",
                duration=30.0,
                text="Olá pessoal. Nossa! Que fail incrível!"
            )

            mock_gemini_instance = MagicMock()
            mock_gemini.return_value = mock_gemini_instance
            mock_gemini_instance.analyze_viral.return_value = ViralAnalysisResult(
                clips=[
                    ViralClip(
                        start=10.0, end=25.0, score=0.95,
                        reason="Reação hilária ao fail no jogo",
                        hook_title="ELE CAIU DE VERDADE? 😱"
                    ),
                ],
                full_transcript="Olá pessoal. Nossa! Que fail incrível!"
            )

            mock_renderer_instance = MagicMock()
            mock_renderer.return_value = mock_renderer_instance
            clip_output = clips_dir / "clip_0.mp4"
            clip_output.write_bytes(b"fake clip content")
            mock_renderer_instance.render_clip.return_value = RenderResult(
                output_path=str(clip_output),
                duration=15.0,
                width=1080,
                height=1920,
            )

            with next(get_session()) as session:
                settings = Settings()
                settings.clips_output_path = str(clips_dir)
                settings.temp_path = str(tmpdir)
                settings.subtitle_style = "karaoke"
                settings.add_hook_titles = True
                settings.virality_threshold = 0.85
                session.add(settings)
                session.commit()

                job = Job(type="vod", source_url="https://twitch.tv/videos/12345")
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
                assert clip.output_path == str(clip_output)
                assert clip.score == 0.95
                assert clip.reason == "Reação hilária ao fail no jogo"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_segment_pipeline():
    """Test live segment processing pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        clips_dir = tmpdir / "clips"
        clips_dir.mkdir()

        # Create a fake source video
        source_video = tmpdir / "live_recording.mp4"
        source_video.write_bytes(b"x" * 1000000)

        with patch("src.workers.orchestrator.extract_live_segment", new_callable=AsyncMock) as mock_extract, \
             patch("src.workers.orchestrator.WhisperWorker") as mock_whisper, \
             patch("src.workers.orchestrator.GeminiWorker") as mock_gemini, \
             patch("src.workers.orchestrator.FFmpegRenderer") as mock_renderer:

            segment_path = tmpdir / "segment.mp4"
            segment_path.write_bytes(b"fake segment")
            mock_extract.return_value = str(segment_path)

            mock_whisper_instance = MagicMock()
            mock_whisper.return_value = mock_whisper_instance
            mock_whisper_instance.transcribe_audio.return_value = TranscriptionResult(
                segments=[
                    Segment(start=0.0, end=30.0, text="Live test content", words=[])
                ],
                language="pt", duration=30.0, text="Live test content"
            )

            mock_gemini_instance = MagicMock()
            mock_gemini.return_value = mock_gemini_instance
            mock_gemini_instance.analyze_viral.return_value = ViralAnalysisResult(
                clips=[
                    ViralClip(start=5.0, end=25.0, score=0.88, reason="Live clip", hook_title="AO VIVO! 🔴")
                ],
                full_transcript="Live test content"
            )

            mock_renderer_instance = MagicMock()
            mock_renderer.return_value = mock_renderer_instance
            clip_output = clips_dir / "live_clip_0.mp4"
            clip_output.write_bytes(b"fake clip")
            mock_renderer_instance.render_clip.return_value = RenderResult(
                output_path=str(clip_output),
                duration=20.0,
                width=1080,
                height=1920,
            )

            with next(get_session()) as session:
                settings = Settings()
                settings.clips_output_path = str(clips_dir)
                settings.temp_path = str(tmpdir)
                settings.live_segment_seconds = 30
                settings.subtitle_style = "karaoke"
                settings.add_hook_titles = True
                session.add(settings)
                session.commit()

                job = Job(type="live_segment", source_path=str(source_video))
                session.add(job)
                session.commit()
                session.refresh(job)

            await process_live_segment_job(None, job.id, str(source_video), 0)

            with next(get_session()) as session:
                job = session.get(Job, job.id)
                assert job.status == "done"
                assert len(job.result_clips) == 1


@pytest.mark.integration
def test_file_watcher_detects_new_file():
    """Test file watcher detects and processes new OBS recording."""
    # This would require a running watcher and actual file system events
    # Marked as integration test to run separately
    pass