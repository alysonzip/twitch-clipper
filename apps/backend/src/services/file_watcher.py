import time
import threading
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from src.models.settings import Settings
from src.services.settings_service import SettingsService
from src.database import get_session


class OBSRecordingHandler(FileSystemEventHandler):
    """Handles file system events for OBS recordings."""

    def __init__(
        self,
        callback: Callable[[str], None],
        debounce_seconds: int = 120,  # 2 minutes default
        valid_extensions: tuple = (".mp4", ".mkv", ".flv", ".mov"),
    ):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.valid_extensions = valid_extensions
        self._last_modified = {}  # path -> timestamp
        self._lock = threading.Lock()
        self._pending_timer: Optional[threading.Timer] = None

    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory:
            self._schedule_check(event.src_path)

    def on_modified(self, event: FileModifiedEvent):
        if not event.is_directory:
            self._schedule_check(event.src_path)

    def _schedule_check(self, file_path: str):
        """Schedule a debounced check for the file."""
        path = Path(file_path)

        # Only process valid video extensions
        if path.suffix.lower() not in self.valid_extensions:
            return

        with self._lock:
            now = time.time()
            self._last_modified[str(path)] = now

            # Cancel existing timer
            if self._pending_timer:
                self._pending_timer.cancel()

            # Schedule new check
            self._pending_timer = threading.Timer(
                self.debounce_seconds,
                self._check_file_stable,
                args=[str(path)]
            )
            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _check_file_stable(self, file_path: str):
        """Check if file has stopped growing (stable)."""
        path = Path(file_path)

        with self._lock:
            last_mod = self._last_modified.get(str(path), 0)

        # Wait a bit more and check file size
        time.sleep(2)

        try:
            current_size = path.stat().st_size
            time.sleep(1)
            new_size = path.stat().st_size

            if current_size == new_size and current_size > 0:
                # File is stable, trigger callback
                self.callback(str(path))
            else:
                # File still growing, reschedule
                self._schedule_check(str(path))
        except (OSError, FileNotFoundError):
            pass  # File deleted or inaccessible


class FileWatcher:
    """Monitors OBS recordings folder for new/updated video files."""

    def __init__(self, session=None):
        self.session = session or next(get_session())
        self.settings_svc = SettingsService(self.session)
        self.observer: Optional[Observer] = None
        self.handler: Optional[OBSRecordingHandler] = None
        self._running = False
        self._paused = False
        self._current_file: Optional[str] = None
        self._last_clip: Optional[str] = None
        self._lock = threading.Lock()

    def start(self):
        """Start watching the configured folder."""
        if self._running:
            return

        settings = self.settings_svc.get()
        watch_path = Path(settings.obs_recordings_path)

        if not watch_path.exists():
            watch_path.mkdir(parents=True, exist_ok=True)

        def on_file_ready(file_path: str):
            if self._paused:
                return

            with self._lock:
                self._current_file = file_path

            # Enqueue live segment job
            self._enqueue_live_segment_job(file_path)

            with self._lock:
                self._last_clip = file_path
                self._current_file = None

        self.handler = OBSRecordingHandler(
            callback=on_file_ready,
            debounce_seconds=settings.live_buffer_minutes * 60,
        )

        self.observer = Observer()
        self.observer.schedule(self.handler, str(watch_path), recursive=False)
        self.observer.start()
        self._running = True

    def stop(self):
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
        self._running = False

    def pause(self):
        """Pause watching (keep observer running, ignore new files)."""
        self._paused = True

    def resume(self):
        """Resume watching."""
        self._paused = False

    def is_running(self) -> bool:
        return self._running

    def is_paused(self) -> bool:
        return self._paused

    def get_status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "paused": self._paused,
                "current_file": self._current_file,
                "last_clip": self._last_clip,
            }

    def _enqueue_live_segment_job(self, video_path: str):
        """Enqueue a live segment processing job."""
        try:
            import redis
            from arq import create_pool
            from src.workers.orchestrator import WorkerSettings

            # This would be called from the ARQ worker context
            # For now, we'll use a simple approach - could be improved with direct ARQ enqueue
            from src.models.job import Job
            from src.database import engine
            from sqlmodel import Session
            import asyncio

            with Session(engine) as session:
                job = Job(
                    type="live_segment",
                    source_path=video_path,
                    status="queued",
                )
                session.add(job)
                session.commit()
                session.refresh(job)

                # In production, enqueue to ARQ:
                # redis_pool = await create_pool(WorkerSettings.redis_settings)
                # await redis_pool.enqueue_job('process_live_segment_job', job.id, video_path, 0)

        except Exception as e:
            print(f"Failed to enqueue live segment job: {e}")