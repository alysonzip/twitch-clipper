import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from src.workers.gemini_worker import GeminiWorker, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.schemas.gemini import ViralAnalysisResult, ViralClip
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


def test_analyze_returns_clips_with_scores():
    """Test viral analysis returns clips with proper structure."""
    with patch("src.workers.gemini_worker.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "clips": [
                {
                    "start": 10.0,
                    "end": 40.0,
                    "score": 0.92,
                    "reason": "Reação hilária ao fail",
                    "hook_title": "ELE CAIU DE VERDADE? 😱"
                },
                {
                    "start": 100.0,
                    "end": 145.0,
                    "score": 0.87,
                    "reason": "Dica valiosa de gameplay",
                    "hook_title": "ESSE TRUQUE MUDA TUDO"
                }
            ]
        })
        mock_model.generate_content.return_value = mock_response

        with next(get_session()) as session:
            settings = Settings()
            settings.gemini_api_key = "test_key"
            session.add(settings)
            session.commit()

        worker = GeminiWorker(session)

        # Create mock transcription
        transcription = TranscriptionResult(
            segments=[
                Segment(start=0.0, end=5.0, text="Olá pessoal", words=[]),
                Segment(start=5.0, end=10.0, text="Vou jogar hoje", words=[]),
                Segment(start=10.0, end=40.0, text="Nossa! Caí do mapa! Que fail!", words=[]),
                Segment(start=100.0, end=145.0, text="A dica é: sempre pule antes de atirar", words=[]),
            ],
            language="pt",
            duration=150.0,
            text="Olá pessoal. Vou jogar hoje. Nossa! Caí do mapa! Que fail! A dica é: sempre pule antes de atirar"
        )

        result = worker.analyze_viral(transcription)

        assert isinstance(result, ViralAnalysisResult)
        assert len(result.clips) == 2
        assert all(isinstance(c, ViralClip) for c in result.clips)
        assert all(0 <= c.score <= 1 for c in result.clips)
        assert all(c.hook_title for c in result.clips)
        assert result.full_transcript == transcription.text


def test_analyze_filters_by_virality_threshold():
    """Test clips below threshold are filtered out."""
    with patch("src.workers.gemini_worker.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "clips": [
                {"start": 10.0, "end": 40.0, "score": 0.95, "reason": "Great", "hook_title": "Hook 1"},
                {"start": 50.0, "end": 80.0, "score": 0.70, "reason": "Okay", "hook_title": "Hook 2"},
                {"start": 100.0, "end": 130.0, "score": 0.60, "reason": "Weak", "hook_title": "Hook 3"},
            ]
        })
        mock_model.generate_content.return_value = mock_response

        with next(get_session()) as session:
            settings = Settings()
            settings.gemini_api_key = "test_key"
            settings.virality_threshold = 0.80
            session.add(settings)
            session.commit()

        worker = GeminiWorker(session)

        transcription = TranscriptionResult(
            segments=[
                Segment(start=0.0, end=150.0, text="Test content", words=[])
            ],
            language="pt",
            duration=150.0,
            text="Test content"
        )

        result = worker.analyze_viral(transcription)

        # Only clips with score >= 0.80 should remain
        assert len(result.clips) == 1
        assert result.clips[0].score == 0.95


def test_analyze_limits_to_five_clips():
    """Test maximum 5 clips returned."""
    with patch("src.workers.gemini_worker.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        # Return 7 clips, should be limited to 5
        clips = [
            {"start": float(i * 10), "end": float(i * 10 + 30), "score": 0.9, "reason": f"Clip {i}", "hook_title": f"Hook {i}"}
            for i in range(7)
        ]
        mock_response = MagicMock()
        mock_response.text = json.dumps({"clips": clips})
        mock_model.generate_content.return_value = mock_response

        with next(get_session()) as session:
            settings = Settings()
            settings.gemini_api_key = "test_key"
            session.add(settings)
            session.commit()

        worker = GeminiWorker(session)

        transcription = TranscriptionResult(
            segments=[Segment(start=0.0, end=200.0, text="Test", words=[])],
            language="pt",
            duration=200.0,
            text="Test"
        )

        result = worker.analyze_viral(transcription)
        assert len(result.clips) == 5


def test_analyze_handles_json_decode_error():
    """Test graceful handling of invalid JSON response."""
    with patch("src.workers.gemini_worker.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = "not valid json {"
        mock_model.generate_content.return_value = mock_response

        with next(get_session()) as session:
            settings = Settings()
            settings.gemini_api_key = "test_key"
            session.add(settings)
            session.commit()

        worker = GeminiWorker(session)

        transcription = TranscriptionResult(
            segments=[Segment(start=0.0, end=10.0, text="Test", words=[])],
            language="pt",
            duration=10.0,
            text="Test"
        )

        with pytest.raises(ValueError, match="Failed to parse Gemini response as JSON"):
            worker.analyze_viral(transcription)


def test_analyze_raises_without_api_key():
    """Test worker raises when API key not configured."""
    with next(get_session()) as session:
        # No settings with API key
        worker = GeminiWorker(session)

        transcription = TranscriptionResult(
            segments=[Segment(start=0.0, end=10.0, text="Test", words=[])],
            language="pt",
            duration=10.0,
            text="Test"
        )

        with pytest.raises(ValueError, match="Gemini API key not configured"):
            worker.analyze_viral(transcription)


def test_system_prompt_contains_viral_criteria():
    """Test system prompt includes all viral criteria."""
    assert "HUMOR" in SYSTEM_PROMPT
    assert "SURPRESA" in SYSTEM_PROMPT
    assert "EMPOÇÃO" in SYSTEM_PROMPT or "EMPOÇÃO" in SYSTEM_PROMPT
    assert "ENSINAMENTO" in SYSTEM_PROMPT
    assert "WTF" in SYSTEM_PROMPT


def test_user_prompt_template_formats_correctly():
    """Test user prompt template formats transcript correctly."""
    transcript = "[0.0-5.0] Hello\n[5.0-10.0] World"
    formatted = USER_PROMPT_TEMPLATE.format(transcript=transcript)

    assert "[0.0-5.0] Hello" in formatted
    assert "[5.0-10.0] World" in formatted
    assert "Responda APENAS com JSON" in formatted