import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.workers.render_worker import FFmpegRenderer, FaceTracker, RenderOptions
from src.schemas.render import RenderResult
from src.schemas.gemini import ViralClip
from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.models.job import Job
from src.models.clip import Clip
from src.models.settings import Settings
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


def test_render_creates_vertical_mp4():
    """Test render creates vertical 1080x1920 MP4."""
    with patch("src.workers.render_worker.ffmpeg") as mock_ffmpeg, \
         patch("src.workers.render_worker.FaceTracker") as mock_face_tracker, \
         patch("src.workers.render_worker.Path.exists", return_value=False):

        # Mock FFmpeg
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.return_value = None

        mock_ffmpeg.probe.return_value = {
            'streams': [{'codec_type': 'video', 'width': 1080, 'height': 1920}]
        }

        # Mock face tracker
        mock_tracker = MagicMock()
        mock_face_tracker.return_value = mock_tracker

        with next(get_session()) as session:
            settings = Settings()
            session.add(settings)
            session.commit()

            renderer = FFmpegRenderer(session)

            clip = ViralClip(
                start=10.0, end=40.0, score=0.9,
                reason="Test", hook_title="Hook Title"
            )

            transcription = TranscriptionResult(
                segments=[Segment(start=10.0, end=40.0, text="Test", words=[])],
                language="pt", duration=30.0, text="Test"
            )

            result = renderer.render_clip(
                source_path="source.mp4",
                clip=clip,
                transcription=transcription,
                output_path="output.mp4",
                options=RenderOptions()
            )

            assert isinstance(result, RenderResult)
            assert result.output_path == "output.mp4"
            assert result.width == 1080
            assert result.height == 1920
            assert result.duration == 30.0


def test_generate_ass_subtitles_karaoke_style():
    """Test ASS subtitle generation with karaoke style."""
    with patch("src.workers.render_worker.FaceTracker"):
        with next(get_session()) as session:
            settings = Settings()
            settings.subtitle_style = "karaoke"
            session.add(settings)
            session.commit()

            renderer = FFmpegRenderer(session)

            transcription = TranscriptionResult(
                segments=[
                    Segment(
                        start=0.0, end=5.0, text="Olá mundo",
                        words=[
                            Word(start=0.0, end=0.5, word="Olá", probability=0.99),
                            Word(start=0.6, end=1.2, word="mundo", probability=0.98),
                        ]
                    )
                ],
                language="pt", duration=5.0, text="Olá mundo"
            )

            ass_path = renderer._generate_ass_subtitles(transcription, "karaoke", Path("output.mp4"))

            assert ass_path.exists()
            content = ass_path.read_text(encoding='utf-8-sig')
            assert "Style: Highlight" in content
            assert "karaoke" in content
            assert "Olá" in content
            assert "mundo" in content

            ass_path.unlink()


def test_generate_ass_subtitles_pop_style():
    """Test ASS subtitle generation with pop style."""
    with patch("src.workers.render_worker.FaceTracker"):
        with next(get_session()) as session:
            settings = Settings()
            settings.subtitle_style = "pop"
            session.add(settings)
            session.commit()

            renderer = FFmpegRenderer(session)

            transcription = TranscriptionResult(
                segments=[
                    Segment(
                        start=0.0, end=5.0, text="Test",
                        words=[Word(start=0.0, end=1.0, word="Test", probability=0.99)]
                    )
                ],
                language="pt", duration=5.0, text="Test"
            )

            ass_path = renderer._generate_ass_subtitles(transcription, "pop", Path("output.mp4"))

            content = ass_path.read_text(encoding='utf-8-sig')
            assert "fade(200)" in content

            ass_path.unlink()


def test_generate_ass_subtitles_minimal_style():
    """Test ASS subtitle generation with minimal style."""
    with patch("src.workers.render_worker.FaceTracker"):
        with next(get_session()) as session:
            settings = Settings()
            settings.subtitle_style = "minimal"
            session.add(settings)
            session.commit()

            renderer = FFmpegRenderer(session)

            transcription = TranscriptionResult(
                segments=[
                    Segment(start=0.0, end=5.0, text="Test content", words=[])
                ],
                language="pt", duration=5.0, text="Test content"
            )

            ass_path = renderer._generate_ass_subtitles(transcription, "minimal", Path("output.mp4"))

            content = ass_path.read_text(encoding='utf-8-sig')
            assert "Test content" in content
            assert "karaoke" not in content
            assert "fade" not in content

            ass_path.unlink()


def test_format_ass_time():
    """Test ASS time formatting."""
    with patch("src.workers.render_worker.FaceTracker"):
        with next(get_session()) as session:
            renderer = FFmpegRenderer(session)

            assert renderer._format_ass_time(0.0) == "0:00:00.00"
            assert renderer._format_ass_time(5.5) == "0:00:05.50"
            assert renderer._format_ass_time(65.0) == "0:01:05.00"
            assert renderer._format_ass_time(3661.25) == "1:01:01.25"


def test_compute_face_crop_filter_no_tracker():
    """Test crop filter falls back to center when no face tracker."""
    with patch("src.workers.render_worker.FaceTracker", return_value=None):
        with next(get_session()) as session:
            renderer = FFmpegRenderer(session)

            filter_str = renderer._compute_face_crop_filter("video.mp4", 1080, 1920)
            assert "crop=1080:1920" in filter_str
            assert "(iw-1080)/2" in filter_str


def test_render_options_defaults():
    """Test RenderOptions default values."""
    opts = RenderOptions()
    assert opts.target_width == 1080
    assert opts.target_height == 1920
    assert opts.fps == 30
    assert opts.subtitle_style == "karaoke"
    assert opts.add_hook_title is True
    assert opts.use_nvenc is True


@pytest.mark.asyncio
async def test_render_job_updates_clips():
    """Test ARQ render_job updates clip statuses."""
    with patch("src.workers.render_worker.FFmpegRenderer") as mock_renderer_class:
        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        mock_result = RenderResult(
            output_path="output.mp4", duration=30.0, width=1080, height=1920
        )
        mock_renderer.render_clip.return_value = mock_result

        with next(get_session()) as session:
            settings = Settings()
            session.add(settings)
            session.commit()

            job = Job(type="vod", source_path="source.mp4")
            session.add(job)
            session.commit()
            session.refresh(job)

            clip = Clip(
                source_path="source.mp4", source_type="vod",
                start=10.0, end=40.0, duration=30.0,
                score=0.9, reason="Test", output_path="output.mp4",
                status="pending"
            )
            session.add(clip)
            session.commit()
            session.refresh(clip)

            job.result_clips = [clip.id]
            session.add(job)
            session.commit()

        from src.workers.render_worker import render_job

        class MockCTX:
            pass

        await render_job(MockCTX(), job.id, [clip.id])

        with next(get_session()) as session:
            job = session.get(Job, job.id)
            assert job.status == "done"
            assert job.progress == 100

            clip = session.get(Clip, clip.id)
            assert clip.status == "done"
            assert clip.output_path == "output.mp4"