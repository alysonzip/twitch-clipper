import json
import google.generativeai as genai

from src.schemas.gemini import ViralAnalysisResult, ViralClip
from src.schemas.whisper import TranscriptionResult
from src.services.settings_service import SettingsService
from src.database import get_session


SYSTEM_PROMPT = """Você é um editor especialista em criar clips virais para TikTok, Reels e Shorts.

Analise a transcrição completa com timestamps e identifique os 3-5 melhores trechos de 15-60 segundos que têm maior potencial viral.

Critérios para viralidade:
- HUMOR: momentos engraçados, piadas, reações cômicas
- SURPRESA: reviravoltas, revelações, "não acredito que fez isso"
- EMOÇÃO: momentos tocantes, inspiradores, raiva justificada
- ENSINAMENTO: dicas valiosas, "life hacks", explicações claras
- MOMENTO "WTF": situações bizarras, inusitadas, caos

Retorne APENAS JSON válido no formato especificado. Não adicione texto extra."""


USER_PROMPT_TEMPLATE = """Transcrição completa da live/VOD:

{transcript}

Identifique os melhores clips virais. Para cada clip, forneça:
- start: timestamp inicial (segundos)
- end: timestamp final (segundos)
- score: 0.0 a 1.0 (potencial viral)
- reason: explicação curta do porquê é viral
- hook_title: título de gancho para os primeiros 3s (máx 50 chars)

Regras:
- Clips entre 15-60 segundos
- Mínimo 3, máximo 5 clips
- Scores devem ser realistas
- Hook titles devem ser "clickbait honesto" - atrativos mas fiéis ao conteúdo

Responda APENAS com JSON:
{{
  "clips": [
    {{"start": 12.3, "end": 45.7, "score": 0.92, "reason": "Reação hilária ao fail no jogo", "hook_title": "ELE CAIU DE VERDADE? 😱"}},
    ...
  ]
}}"""


class GeminiWorker:
    def __init__(self, session=None):
        self.session = session or next(get_session())
        self.settings_svc = SettingsService(self.session)
        self._model = None

    @property
    def model(self):
        if self._model is None:
            settings = self.settings_svc.get()
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key not configured")

            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(
                "gemini-1.5-flash-latest",
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                },
            )
        return self._model

    def analyze_viral(self, transcription: TranscriptionResult) -> ViralAnalysisResult:
        """Analyze transcription and return viral clip candidates."""
        # Build transcript with timestamps
        transcript_lines = []
        for seg in transcription.segments:
            transcript_lines.append(f"[{seg.start:.1f}-{seg.end:.1f}] {seg.text}")

        transcript_text = "\n".join(transcript_lines)

        prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript_text)

        response = self.model.generate_content([
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "user", "parts": [prompt]},
        ])

        # Parse JSON response
        try:
            data = json.loads(response.text)
            clips = [ViralClip(**clip) for clip in data.get("clips", [])]

            # Filter by score threshold
            settings = self.settings_svc.get()
            clips = [c for c in clips if c.score >= settings.virality_threshold]

            # Limit to 5 clips
            clips = clips[:5]

            return ViralAnalysisResult(
                clips=clips,
                full_transcript=transcription.text,
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process Gemini response: {e}")


# ARQ Job function
async def analyze_viral_job(ctx, job_id: int, transcription_data: dict):
    """ARQ job to analyze transcription for viral clips."""
    from src.models.job import Job
    from src.database import engine
    from sqlmodel import Session, select
    from src.schemas.whisper import TranscriptionResult, Segment, Word

    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return

        job.current_step = "analyzing"
        job.progress = 60
        session.add(job)
        session.commit()

        try:
            # Reconstruct transcription result from stored data
            transcription = TranscriptionResult(**transcription_data)

            worker = GeminiWorker(session)
            result = worker.analyze_viral(transcription)

            # Store analysis result for render job
            # In real implementation, this would be saved to DB or passed to next job
            job.current_step = "analyzed"
            job.progress = 75
            session.add(job)
            session.commit()

        except Exception as e:
            job.status = "failed"
            job.error = f"Viral analysis failed: {str(e)}"
            session.add(job)
            session.commit()
            raise