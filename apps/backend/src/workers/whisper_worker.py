import os
from pathlib import Path
from faster_whisper import WhisperModel

from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.services.settings_service import SettingsService
from src.database import get_session


class WhisperWorker:
    def __init__(self, session=None):
        self.session = session or next(get_session())
        self.settings_svc = SettingsService(self.session)
        self._model = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            settings = self.settings_svc.get()
            model_name = settings.whisper_model

            # Use bundled model if available, otherwise download
            base_dir = Path(__file__).parent.parent.parent.parent  # project root
            model_dir = base_dir / "resources" / "models" / f"whisper-{model_name}-int8"

            if model_dir.exists():
                model_path = str(model_dir)
            else:
                model_path = model_name  # Will download from HF

            self._model = WhisperModel(
                model_path,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                cpu_threads=os.cpu_count() or 4,
            )
        return self._model

    def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file and return result with word-level timestamps."""
        segments, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            vad_filter=True,
            language="pt",  # Default to Portuguese, could be configurable
        )

        result_segments = []
        full_text_parts = []

        for segment in segments:
            words = []
            if segment.words:
                for word in segment.words:
                    words.append(Word(
                        start=word.start,
                        end=word.end,
                        word=word.word,
                        probability=word.probability,
                    ))

            result_segments.append(Segment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                words=words,
            ))
            full_text_parts.append(segment.text.strip())

        return TranscriptionResult(
            segments=result_segments,
            language=info.language,
            duration=info.duration,
            text=" ".join(full_text_parts),
        )

    def transcribe_segment(self, audio_path: str, start: float, end: float) -> TranscriptionResult:
        """Transcribe a specific segment of audio file."""
        # For now, transcribe full and filter - could be optimized with ffmpeg seek
        result = self.transcribe_audio(audio_path)
        filtered_segments = [
            s for s in result.segments
            if s.end >= start and s.start <= end
        ]
        return TranscriptionResult(
            segments=filtered_segments,
            language=result.language,
            duration=end - start,
            text=" ".join(s.text for s in filtered_segments),
        )


# ARQ Job function
async def transcribe_job(ctx, job_id: int):
    """ARQ job to transcribe audio for a job."""
    from src.models.job import Job
    from src.database import engine
    from sqlmodel import Session, select

    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return

        job.status = "processing"
        job.current_step = "transcribing"
        job.progress = 10
        session.add(job)
        session.commit()

        try:
            worker = WhisperWorker(session)
            result = worker.transcribe_audio(job.source_path)

            # Store transcription result (could be saved to file or DB)
            # For now, we'll pass it to the next job via job metadata
            job.current_step = "transcribed"
            job.progress = 50
            session.add(job)
            session.commit()

        except Exception as e:
            job.status = "failed"
            job.error = f"Transcription failed: {str(e)}"
            session.add(job)
            session.commit()
            raise