import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional
import ffmpeg

from src.schemas.render import RenderOptions, RenderResult
from src.schemas.gemini import ViralClip
from src.schemas.whisper import TranscriptionResult, Segment, Word
from src.services.settings_service import SettingsService
from src.database import get_session


class FaceTracker:
    """YOLOv8n face detection with ONNX Runtime DirectML."""

    def __init__(self, model_path: str):
        try:
            import onnxruntime as ort
            providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape  # [1, 3, 640, 640]
        except ImportError:
            self.session = None
            print("Warning: onnxruntime not available, face tracking disabled")

    def detect_faces(self, frame) -> List[tuple]:
        """Detect faces in frame. Returns list of (x1, y1, x2, y2, confidence)."""
        if self.session is None:
            return []

        import cv2
        import numpy as np

        # Preprocess
        h, w = frame.shape[:2]
        input_h, input_w = self.input_shape[2], self.input_shape[3]

        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (input_w, input_h), swapRB=True, crop=False)

        # Run inference
        outputs = self.session.run([self.output_name], {self.input_name: blob})[0]

        # Parse YOLOv8 output: [batch, num_boxes, 4+num_classes]
        # For face detection, usually 1 class (face)
        faces = []
        for det in outputs[0]:
            x_center, y_center, width, height, conf = det[:5]
            if conf < 0.5:  # confidence threshold
                continue

            # Convert to original frame coordinates
            x1 = int((x_center - width/2) * w / input_w)
            y1 = int((y_center - height/2) * h / input_h)
            x2 = int((x_center + width/2) * w / input_w)
            y2 = int((y_center + height/2) * h / input_h)

            faces.append((x1, y1, x2, y2, float(conf)))

        return faces


class FFmpegRenderer:
    def __init__(self, session=None):
        self.session = session or next(get_session())
        self.settings_svc = SettingsService(self.session)

        # Initialize face tracker if model available
        base_dir = Path(__file__).parent.parent.parent.parent
        model_path = base_dir / "resources" / "models" / "yolov8n-face.onnx"
        self.face_tracker = FaceTracker(str(model_path)) if model_path.exists() else None

    def _generate_ass_subtitles(self, transcription: TranscriptionResult, style: str, output_path: Path) -> Path:
        """Generate ASS subtitle file from word-level transcription."""
        ass_path = output_path.with_suffix('.ass')

        # ASS header
        header = """[Script Info]
Title: Twitch Clipper Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Bold,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,20,20,80,1
Style: Highlight,Montserrat Bold,60,&H00FFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,20,20,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for segment in transcription.segments:
            if not segment.words:
                # No word timestamps, use segment as whole
                start = self._format_ass_time(segment.start)
                end = self._format_ass_time(segment.end)
                text = segment.text.replace('\n', '\\N')
                events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
            else:
                if style == "karaoke":
                    # Karaoke: highlight each word as it's spoken
                    for word in segment.words:
                        start = self._format_ass_time(word.start)
                        end = self._format_ass_time(word.end)
                        word_text = word.word.strip()
                        events.append(f"Dialogue: 0,{start},{end},Highlight,,0,0,0,karaoke,{word_text}")
                elif style == "pop":
                    # Pop: word appears suddenly
                    for word in segment.words:
                        start = self._format_ass_time(word.start)
                        end = self._format_ass_time(word.end)
                        word_text = word.word.strip()
                        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,fade(200),{word_text}")
                else:  # minimal
                    start = self._format_ass_time(segment.start)
                    end = self._format_ass_time(segment.end)
                    text = segment.text.replace('\n', '\\N')
                    events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        with open(ass_path, 'w', encoding='utf-8-sig') as f:
            f.write(header + "\n".join(events))

        return ass_path

    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format H:MM:SS.cc"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def _compute_face_crop_filter(self, video_path: str, target_w: int, target_h: int) -> str:
        """Generate FFmpeg crop filter with face tracking."""
        if self.face_tracker is None:
            # Center crop fallback
            return f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"

        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Sample frames for face detection (every 15 frames = 0.5s at 30fps)
        sample_interval = 15
        face_positions = []

        for frame_idx in range(0, frame_count, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            faces = self.face_tracker.detect_faces(frame)
            if faces:
                # Use largest face
                largest = max(faces, key=lambda f: (f[2]-f[0])*(f[3]-f[1]))
                cx = (largest[0] + largest[2]) / 2
                cy = (largest[1] + largest[3]) / 2
                face_positions.append((frame_idx, cx, cy))

        cap.release()

        if not face_positions:
            return f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"

        # Smooth face positions (simple moving average)
        window = 5
        smoothed = []
        for i in range(len(face_positions)):
            start = max(0, i - window//2)
            end = min(len(face_positions), i + window//2 + 1)
            avg_x = sum(p[1] for p in face_positions[start:end]) / (end - start)
            avg_y = sum(p[2] for p in face_positions[start:end]) / (end - start)
            smoothed.append((face_positions[i][0], avg_x, avg_y))

        # Build crop filter with sendcmd for dynamic cropping
        # This is complex; for now use center of average face position
        avg_cx = sum(p[1] for p in smoothed) / len(smoothed)
        avg_cy = sum(p[2] for p in smoothed) / len(smoothed)

        # Clamp to valid crop region
        cap = cv2.VideoCapture(video_path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        crop_x = max(0, min(w - target_w, int(avg_cx - target_w / 2)))
        crop_y = max(0, min(h - target_h, int(avg_cy - target_h / 2)))

        return f"crop={target_w}:{target_h}:{crop_x}:{crop_y}"

    def render_clip(
        self,
        source_path: str,
        clip: ViralClip,
        transcription: TranscriptionResult,
        output_path: str,
        options: Optional[RenderOptions] = None
    ) -> RenderResult:
        """Render vertical clip with face crop, subtitles, and hook title."""
        options = options or RenderOptions()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Generate subtitles
        ass_path = self._generate_ass_subtitles(transcription, options.subtitle_style, output)

        # Compute face crop filter
        crop_filter = self._compute_face_crop_filter(
            source_path, options.target_width, options.target_height
        )

        # Build FFmpeg filter chain
        filters = [
            crop_filter,
            f"scale={options.target_width}:{options.target_height}:force_original_aspect_ratio=decrease",
            f"pad={options.target_width}:{options.target_height}:(ow-iw)/2:(oh-ih)/2",
            f"fps={options.fps}",
            f"subtitles={ass_path.as_posix()}",
        ]

        # Add hook title if enabled
        if options.add_hook_title and clip.hook_title:
            # Draw hook title for first 3 seconds
            hook_filter = (
                f"drawtext=text='{clip.hook_title}':"
                f"fontfile={options.font_path or 'Montserrat-Bold.ttf'}:"
                f"fontsize=72:fontcolor=white:borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y=h*0.15:"
                f"enable='between(t,0,3)':"
                f"alpha='if(lt(t,0.5),t*2,if(gt(t,2.5),1-(t-2.5)*2,1))'"
            )
            filters.append(hook_filter)

        filter_complex = ",".join(filters)

        # Choose encoder
        settings = self.settings_svc.get()
        use_nvenc = options.use_nvenc

        try:
            # Try NVENC first
            stream = ffmpeg.input(source_path, ss=clip.start, t=clip.end - clip.start)
            stream = stream.output(
                output_path,
                vf=filter_complex,
                vcodec='h264_nvenc' if use_nvenc else 'libx264',
                acodec='aac',
                audio_bitrate='128k',
                preset='p4' if use_nvenc else 'medium',
                crf=23 if not use_nvenc else None,
                **({'rc': 'vbr', 'cq': '25'} if use_nvenc else {})
            )
            stream = stream.overwrite_output()
            stream.run(capture_stdout=True, capture_stderr=True)

        except ffmpeg.Error as e:
            if use_nvenc:
                # Fallback to libx264
                print("NVENC failed, falling back to libx264")
                stream = ffmpeg.input(source_path, ss=clip.start, t=clip.end - clip.start)
                stream = stream.output(
                    output_path,
                    vf=filter_complex,
                    vcodec='libx264',
                    acodec='aac',
                    audio_bitrate='128k',
                    preset='medium',
                    crf=23
                )
                stream = stream.overwrite_output()
                stream.run(capture_stdout=True, capture_stderr=True)
            else:
                raise

        # Cleanup ASS file
        try:
            ass_path.unlink()
        except:
            pass

        # Verify output
        probe = ffmpeg.probe(output_path)
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')

        return RenderResult(
            output_path=output_path,
            duration=clip.end - clip.start,
            width=int(video_stream['width']),
            height=int(video_stream['height']),
        )


# ARQ Job function
async def render_job(ctx, job_id: int, clip_ids: List[int]):
    """ARQ job to render clips."""
    from src.models.job import Job
    from src.models.clip import Clip
    from src.database import engine
    from sqlmodel import Session, select

    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return

        job.current_step = "rendering"
        job.progress = 80
        session.add(job)
        session.commit()

        try:
            clips = session.exec(select(Clip).where(Clip.id.in_(clip_ids))).all()
            transcription_data = {}  # Would be passed from previous job

            renderer = FFmpegRenderer(session)
            settings = session.get(Settings, 1)

            options = RenderOptions(
                subtitle_style=settings.subtitle_style,
                add_hook_titles=settings.add_hook_titles,
            )

            for clip in clips:
                # Update clip status
                clip.status = "processing"
                session.add(clip)

                # Render
                result = renderer.render_clip(
                    source_path=job.source_path,
                    clip=clip,
                    transcription=TranscriptionResult(**transcription_data),
                    output_path=clip.output_path,
                    options=options
                )

                clip.status = "done"
                clip.output_path = result.output_path
                session.add(clip)

            job.status = "done"
            job.progress = 100
            job.current_step = "completed"
            job.result_clips = [c.id for c in clips]
            session.add(job)
            session.commit()

        except Exception as e:
            job.status = "failed"
            job.error = f"Rendering failed: {str(e)}"
            session.add(job)
            session.commit()
            raise