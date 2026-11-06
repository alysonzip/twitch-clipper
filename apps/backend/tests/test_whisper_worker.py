import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.workers.whisper_worker import WhisperWorker
from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.models.job import Job
from src.models.settings import Settings
from src.database import engine, init_db, get_session


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    with next(get_session()) as session:
        session.exec(select(Job)).delete()
        session.exec(select(Settings)).delete()
        session.commit()


def test_transcribe_returns_segments_with_words():
    """Test transcription returns proper structure with word-level timestamps."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        # Mock the model
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        # Mock transcription result
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Olá mundo"

        mock_word1 = MagicMock()
        mock_word1.start = 0.0
        mock_word1.end = 0.5
        mock_word1.word = "Olá"
        mock_word1.probability = 0.99

        mock_word2 = MagicMock()
        mock_word2.start = 0.6
        mock_word2.end = 1.2
        mock_word2.word = "mundo"
        mock_word2.probability = 0.98

        mock_segment.words = [mock_word1, mock_word2]

        mock_info = MagicMock()
        mock_info.language = "pt"
        mock_info.duration = 5.0

        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        # Test
        worker = WhisperWorker()
        result = worker.transcribe_audio("test_audio.wav")

        assert isinstance(result, TranscriptionResult)
        assert len(result.segments) == 1
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 5.0
        assert result.segments[0].text == "Olá mundo"
        assert len(result.segments[0].words) == 2
        assert result.segments[0].words[0].word == "Olá"
        assert result.segments[0].words[1].word == "mundo"
        assert result.language == "pt"
        assert result.duration == 5.0
        assert result.text == "Olá mundo"


def test_transcribe_handles_empty_words():
    """Test transcription handles segments without word timestamps."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Olá mundo"
        mock_segment.words = None

        mock_info = MagicMock()
        mock_info.language = "pt"
        mock_info.duration = 5.0

        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        worker = WhisperWorker()
        result = worker.transcribe_audio("test_audio.wav")

        assert len(result.segments) == 1
        assert result.segments[0].words == []


def test_transcribe_multiple_segments():
    """Test transcription with multiple segments."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        segments = []
        for i in range(3):
            seg = MagicMock()
            seg.start = float(i * 5)
            seg.end = float((i + 1) * 5)
            seg.text = f"Segmento {i + 1}"
            seg.words = []
            segments.append(seg)

        mock_info = MagicMock()
        mock_info.language = "pt"
        mock_info.duration = 15.0

        mock_model.transcribe.return_value = (segments, mock_info)

        worker = WhisperWorker()
        result = worker.transcribe_audio("test_audio.wav")

        assert len(result.segments) == 3
        assert result.duration == 15.0


@pytest.mark.asyncio
async def test_transcribe_job_updates_job_status():
    """Test ARQ transcribe_job updates job status correctly."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Test"
        mock_segment.words = []

        mock_info = MagicMock()
        mock_info.language = "pt"
        mock_info.duration = 5.0

        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        # Create job in DB
        with next(get_session()) as session:
            job = Job(type="vod", source_path="test.mp4")
            session.add(job)
            session.commit()
            session.refresh(job)
            job_id = job.id

        # Run job
        from src.workers.whisper_worker import transcribe_job

        class MockCTX:
            pass

        await transcribe_job(MockCTX(), job_id)

        # Verify job updated
        with next(get_session()) as session:
            job = session.get(Job, job_id)
            assert job.status == "processing"
            assert job.current_step == "transcribed"
            assert job.progress == 50


def test_worker_loads_bundled_model_when_available(tmp_path):
    """Test worker loads bundled model when available."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        # Create fake bundled model directory
        base_dir = Path(__file__).parent.parent.parent.parent
        model_dir = base_dir / "resources" / "models" / "whisper-base-int8"
        model_dir.mkdir(parents=True, exist_ok=True)

        worker = WhisperWorker()
        _ = worker.model  # Access property to trigger loading

        # Verify WhisperModel called with bundled path
        mock_model_class.assert_called_once()
        args, kwargs = mock_model_class.call_args
        assert "whisper-base-int8" in args[0]


def test_worker_uses_settings_for_config():
    """Test worker uses settings for model config."""
    with patch("src.workers.whisper_worker.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        # Create settings with custom config
        with next(get_session()) as session:
            settings = Settings()
            settings.whisper_model = "small"
            settings.whisper_device = "cpu"
            settings.whisper_compute_type = "int8"
            session.add(settings)
            session.commit()

        worker = WhisperWorker()
        _ = worker.model

        mock_model_class.assert_called_once()
        args, kwargs = mock_model_class.call_args
        assert "small" in args[0] or args[0] == "small"
        assert kwargs["device"] == "cpu"
        assert kwargs["compute_type"] == "int8"