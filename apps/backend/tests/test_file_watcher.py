import pytest
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.file_watcher import OBSRecordingHandler, FileWatcher
from src.models.settings import Settings
from src.database import engine, init_db, get_session


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    with next(get_session()) as session:
        session.exec(select(Settings)).delete()
        session.commit()


def test_watcher_triggers_on_stable_file(tmp_path):
    """Test watcher triggers callback when file stabilizes."""
    events = []
    handler = OBSRecordingHandler(
        callback=lambda p: events.append(p),
        debounce_seconds=1,  # Short for testing
    )

    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"x" * 1000)

    # Simulate file creation
    handler.on_created(type('Event', (), {'src_path': str(test_file), 'is_directory': False})())

    # Wait for debounce + stability check
    time.sleep(2.5)

    assert len(events) == 1
    assert events[0] == str(test_file)


def test_watcher_ignores_invalid_extensions(tmp_path):
    """Test watcher ignores non-video files."""
    events = []
    handler = OBSRecordingHandler(callback=lambda p: events.append(p), debounce_seconds=0.5)

    test_file = tmp_path / "test.txt"
    test_file.write_text("not a video")

    handler.on_created(type('Event', (), {'src_path': str(test_file), 'is_directory': False})())

    time.sleep(1.5)
    assert len(events) == 0


def test_watcher_debounces_multiple_modifications(tmp_path):
    """Test watcher debounces rapid modifications."""
    events = []
    handler = OBSRecordingHandler(callback=lambda p: events.append(p), debounce_seconds=0.5)

    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"x" * 100)

    # Simulate rapid modifications
    for i in range(5):
        handler.on_modified(type('Event', (), {'src_path': str(test_file), 'is_directory': False})())
        test_file.write_bytes(b"x" * (100 + i * 10))
        time.sleep(0.1)

    # Wait for debounce
    time.sleep(2)

    # Should only trigger once after file stabilizes
    assert len(events) == 1


def test_file_watcher_start_stop():
    """Test FileWatcher start/stop lifecycle."""
    with patch("src.services.file_watcher.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_settings_svc = MagicMock()
        with patch("src.services.file_watcher.SettingsService", return_value=mock_settings_svc):
            mock_settings_svc.get.return_value = Settings(
                obs_recordings_path=str(Path(__file__).parent.parent / "tmp_obs"),
                live_buffer_minutes=1,
            )

            watcher = FileWatcher()
            watcher.start()
            assert watcher.is_running() is True
            assert watcher.is_paused() is False

            watcher.stop()
            assert watcher.is_running() is False


def test_file_watcher_pause_resume():
    """Test FileWatcher pause/resume."""
    with patch("src.services.file_watcher.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_settings_svc = MagicMock()
        with patch("src.services.file_watcher.SettingsService", return_value=mock_settings_svc):
            mock_settings_svc.get.return_value = Settings(
                obs_recordings_path=str(Path(__file__).parent.parent / "tmp_obs"),
                live_buffer_minutes=1,
            )

            watcher = FileWatcher()
            watcher.start()

            watcher.pause()
            assert watcher.is_paused() is True

            watcher.resume()
            assert watcher.is_paused() is False

            watcher.stop()


def test_file_watcher_status():
    """Test FileWatcher get_status returns correct info."""
    with patch("src.services.file_watcher.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_settings_svc = MagicMock()
        with patch("src.services.file_watcher.SettingsService", return_value=mock_settings_svc):
            mock_settings_svc.get.return_value = Settings(
                obs_recordings_path=str(Path(__file__).parent.parent / "tmp_obs"),
                live_buffer_minutes=1,
            )

            watcher = FileWatcher()
            watcher.start()

            status = watcher.get_status()
            assert status["running"] is True
            assert status["paused"] is False
            assert status["current_file"] is None
            assert status["last_clip"] is None

            watcher.stop()