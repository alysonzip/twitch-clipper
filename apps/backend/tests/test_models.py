import pytest
from datetime import datetime
from sqlmodel import Session, select

from src.models.clip import Clip
from src.models.job import Job
from src.models.settings import Settings
from src.database import engine, init_db, get_session


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test."""
    init_db()
    yield
    # Clean up after test
    with Session(engine) as session:
        session.exec(select(Clip)).delete()
        session.exec(select(Job)).delete()
        session.commit()


def test_clip_model_creates_with_defaults():
    """Test Clip model creates with default values."""
    with Session(engine) as session:
        clip = Clip(source_path="test.mp4", start=10.0, end=40.0, score=0.9)
        session.add(clip)
        session.commit()
        session.refresh(clip)

        assert clip.id is not None
        assert clip.source_path == "test.mp4"
        assert clip.start == 10.0
        assert clip.end == 40.0
        assert clip.duration == 30.0
        assert clip.score == 0.9
        assert clip.status == "pending"
        assert clip.created_at is not None
        assert isinstance(clip.created_at, datetime)


def test_job_model_creates_with_defaults():
    """Test Job model creates with default values."""
    with Session(engine) as session:
        job = Job(type="vod", source_url="https://twitch.tv/videos/123")
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.id is not None
        assert job.type == "vod"
        assert job.source_url == "https://twitch.tv/videos/123"
        assert job.status == "queued"
        assert job.progress == 0
        assert job.result_clips == []
        assert job.created_at is not None
        assert isinstance(job.created_at, datetime)


def test_settings_model_creates_singleton():
    """Test Settings model creates singleton row with defaults."""
    with Session(engine) as session:
        settings = Settings()
        session.add(settings)
        session.commit()
        session.refresh(settings)

        assert settings.id == 1
        assert settings.obs_recordings_path == r"E:\OBS\Recordings"
        assert settings.clips_output_path == r"E:\clips\prontos"
        assert settings.temp_path == r"E:\clips\processando"
        assert settings.whisper_model == "base"
        assert settings.virality_threshold == 0.85
        assert settings.min_clip_duration == 15
        assert settings.max_clip_duration == 60
        assert settings.add_hook_titles is True
        assert settings.add_broll is False
        assert settings.subtitle_style == "karaoke"
        assert settings.auto_start is False


def test_settings_singleton_enforced():
    """Test only one Settings row can exist (id=1 primary key)."""
    with Session(engine) as session:
        settings1 = Settings()
        settings2 = Settings()
        session.add(settings1)
        session.add(settings2)

        with pytest.raises(Exception):
            session.commit()


def test_clip_status_transitions():
    """Test Clip status can be updated through workflow."""
    with Session(engine) as session:
        clip = Clip(source_path="test.mp4", start=0.0, end=30.0, score=0.95)
        session.add(clip)
        session.commit()
        session.refresh(clip)

        # pending -> processing
        clip.status = "processing"
        session.add(clip)
        session.commit()
        session.refresh(clip)
        assert clip.status == "processing"

        # processing -> done
        clip.status = "done"
        clip.output_path = r"E:\clips\prontos\clip_1.mp4"
        clip.completed_at = datetime.utcnow()
        session.add(clip)
        session.commit()
        session.refresh(clip)
        assert clip.status == "done"
        assert clip.output_path is not None
        assert clip.completed_at is not None


def test_job_progress_tracking():
    """Test Job progress can be tracked through steps."""
    with Session(engine) as session:
        job = Job(type="live_segment")
        session.add(job)
        session.commit()
        session.refresh(job)

        # queued -> processing
        job.status = "processing"
        job.progress = 25
        job.current_step = "downloading"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.status == "processing"
        assert job.progress == 25

        # processing -> done with result clips
        job.status = "done"
        job.progress = 100
        job.current_step = "completed"
        job.result_clips = [1, 2, 3]
        job.completed_at = datetime.utcnow()
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.status == "done"
        assert job.progress == 100
        assert job.result_clips == [1, 2, 3]