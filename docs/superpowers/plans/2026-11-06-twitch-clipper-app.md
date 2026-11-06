# Twitch Clipper App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Windows app (Electron + Python backend) that monitors OBS recordings on disk E:, processes Twitch VODs, and uses local Whisper + cloud Gemini Flash to create viral-ready vertical 9:16 clips with karaoke subtitles, face-centered crop, and hook titles.

**Architecture:** Electron GUI (React/Vite) manages settings, history, player, and system tray. Python backend (FastAPI + ARQ/Redis) runs Whisper (faster-whisper, CPU), Gemini Flash (viral scoring), and FFmpeg renderer (vertical crop, YOLOv8n face tracking, karaoke subtitles). File watcher monitors `E:\OBS\Recordings\` for real-time processing. Twitch OAuth fetches VODs for post-stream processing. Packaged as NSIS installer via PyInstaller + Electron Builder.

**Tech Stack:** Electron 28+, React 18, Vite, TypeScript, TailwindCSS; Python 3.11+, FastAPI, ARQ, Redis, faster-whisper, google-generativeai, ffmpeg-python, onnxruntime-directml (YOLOv8n), sqlmodel (SQLite); PyInstaller, Electron Builder (NSIS).

**Spec:** This plan implements the design approved in conversation on 2026-11-06 (hybrid approach: local Whisper + Gemini Flash, RX 550 4GB compatible, full GUI, standalone exe).

## Global Constraints

- Python >= 3.11, Node >= 20
- All local models bundled in installer (Whisper base.int8, YOLOv8n-face ONNX, ffmpeg static)
- GPU: DirectML for YOLOv8n; Whisper runs CPU (int8) via faster-whisper
- Gemini Flash API key required (free tier 1500 req/day) — entered in GUI settings
- Twitch OAuth: Client ID/Secret stored encrypted via Windows DPAPI
- Output folder: `E:\clips\prontos\` (configurable); temp: `E:\clips\processando\`
- Real-time latency target: 2-5 minutes (configurable buffer)
- Clip format: MP4, H.264 NVENC, 1080x1920 (9:16), 30fps, karaoke subtitles burned in
- Virality score threshold: default 0.85 (configurable 0.5-0.99)
- Min clip: 15s, Max clip: 60s (configurable)
- Auto-start with Windows (optional, via registry Run key)
- System tray: show status, open GUI, pause/resume watcher, open clips folder
- All paths use raw strings / pathlib; no hardcoded drive letters except defaults

## Review Focus

1. **Missing Gemini API key** — App should show clear setup wizard on first run, not crash silently
2. **OBS not recording / folder empty** — File watcher should show "aguardando gravação" state, not error
3. **Whisper model download fails** — Bundled models must work offline; fallback to download only if missing
4. **FFmpeg NVENC unavailable** — Auto-fallback to libx264 CPU with warning in logs
5. **Twitch token expired** — Auto-refresh via refresh_token; if fails, prompt re-login in GUI

---

### Task 1: Project Scaffold & Monorepo Structure

**Files:**
- Create: `package.json` (root, npm workspaces)
- Create: `apps/frontend/package.json`
- Create: `apps/backend/pyproject.toml`
- Create: `apps/backend/src/__init__.py`
- Create: `apps/backend/src/main.py`
- Create: `apps/frontend/vite.config.ts`
- Create: `apps/frontend/tsconfig.json`
- Create: `apps/frontend/index.html`
- Create: `apps/frontend/src/main.tsx`
- Create: `apps/frontend/src/App.tsx`
- Create: `docker-compose.yml` (dev Redis)
- Create: `.env.example`
- Create: `README.md`

**Interfaces:**
- Consumes: none
- Produces: monorepo structure, dev scripts (`npm run dev`, `npm run backend`, `npm run build`)

- [ ] **Step 1: Write root package.json with workspaces**

```json
{
  "name": "twitch-clipper",
  "private": true,
  "workspaces": ["apps/frontend", "apps/backend"],
  "scripts": {
    "dev": "concurrently \"npm run dev:frontend\" \"npm run dev:backend\"",
    "dev:frontend": "npm run dev --workspace=apps/frontend",
    "dev:backend": "npm run dev --workspace=apps/backend",
    "build": "npm run build --workspaces",
    "package": "npm run package --workspaces"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
```

- [ ] **Step 2: Write backend pyproject.toml**

```toml
[project]
name = "twitch-clipper-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi==0.111.0",
  "uvicorn[standard]==0.30.1",
  "arq==0.23.1",
  "redis==5.0.1",
  "sqlmodel==0.0.21",
  "pydantic==2.7.4",
  "pydantic-settings==2.3.4",
  "python-multipart==0.0.9",
  "python-dotenv==1.0.1",
  "httpx==0.27.0",
  "google-generativeai==0.7.2",
  "faster-whisper==1.0.3",
  "ffmpeg-python==0.2.0",
  "onnxruntime-directml==1.18.0",
  "opencv-python-headless==4.10.0.84",
  "numpy==1.26.4",
  "yt-dlp==2024.7.4",
  "cryptography==42.0.8",
  "keyring==25.1.0",
  "pywin32==306",
  "watchdog==4.0.1",
  "pyinstaller==6.8.0"
]

[tool.uv]
dev-dependencies = ["pytest==8.2.2", "pytest-asyncio==0.23.3", "httpx==0.27.0", "ruff==0.5.5"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 3: Write frontend package.json**

```json
{
  "name": "twitch-clipper-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "package": "electron-builder"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "zustand": "^4.5.5",
    "lucide-react": "^0.441.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.9",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "electron": "^30.0.1",
    "electron-builder": "^24.13.3",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.12",
    "typescript": "^5.6.2",
    "vite": "^5.4.8",
    "wait-on": "^8.0.1"
  },
  "build": {
    "appId": "com.twitchclipper.app",
    "productName": "Twitch Clipper",
    "directories": { "output": "dist_electron" },
    "files": ["dist/**/*", "backend/**/*"],
    "extraResources": [
      { "from": "apps/backend/dist", "to": "backend", "filter": ["**/*"] }
    ],
    "win": {
      "target": "nsis",
      "icon": "build/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "perMachine": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "Twitch Clipper"
    }
  }
}
```

- [ ] **Step 4: Write frontend vite.config.ts, tsconfig.json, index.html, main.tsx, App.tsx (minimal React + Tailwind setup)**
- [ ] **Step 5: Write backend main.py (FastAPI app factory, lifespan, router imports)**
- [ ] **Step 6: Write docker-compose.yml (Redis only for dev)**
- [ ] **Step 7: Run `npm install` and `uv sync` in backend; verify `npm run dev` starts both**

---

### Task 2: Database Models & Settings Schema

**Files:**
- Create: `apps/backend/src/models/__init__.py`
- Create: `apps/backend/src/models/clip.py`
- Create: `apps/backend/src/models/job.py`
- Create: `apps/backend/src/models/settings.py`
- Create: `apps/backend/src/database.py`
- Create: `apps/backend/tests/test_models.py`

**Interfaces:**
- Consumes: Task 1 (project structure)
- Produces: SQLModel tables (`Clip`, `Job`, `Settings`), `get_session()` dependency, `init_db()` function

- [ ] **Step 1: Write failing test for Clip model**

```python
def test_clip_model_creates_with_defaults():
    clip = Clip(source_path="test.mp4", start=10.0, end=40.0, score=0.9)
    assert clip.id is None
    assert clip.status == "pending"
    assert clip.created_at is not None
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement models in `clip.py`, `job.py`, `settings.py`**

```python
# clip.py
class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_path: str
    source_type: str  # "vod" | "live"
    start: float
    end: float
    duration: float
    score: float
    reason: str
    output_path: Optional[str] = None
    status: str = "pending"  # pending, processing, done, failed
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# job.py
class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # "vod" | "live_segment"
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    status: str = "queued"
    progress: int = 0
    current_step: str = ""
    result_clips: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# settings.py
class Settings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)  # singleton
    obs_recordings_path: str = r"E:\OBS\Recordings"
    clips_output_path: str = r"E:\clips\prontos"
    temp_path: str = r"E:\clips\processando"
    twitch_client_id: Optional[str] = None
    twitch_client_secret_encrypted: Optional[str] = None
    twitch_access_token: Optional[str] = None
    twitch_refresh_token: Optional[str] = None
    gemini_api_key: Optional[str] = None
    whisper_model: str = "base"  # tiny, base, small
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    virality_threshold: float = 0.85
    min_clip_duration: int = 15
    max_clip_duration: int = 60
    live_buffer_minutes: int = 2
    live_segment_seconds: int = 30
    add_hook_titles: bool = True
    add_broll: bool = False
    subtitle_style: str = "karaoke"  # karaoke, pop, minimal
    auto_start: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Implement `database.py` with `engine`, `get_session()`, `init_db()`**
- [ ] **Step 5: Run tests; verify tables create**

---

### Task 3: Settings Service (DPAPI Encryption + Singleton)

**Files:**
- Create: `apps/backend/src/services/settings_service.py`
- Create: `apps/backend/tests/test_settings_service.py`

**Interfaces:**
- Consumes: Task 2 (Settings model, get_session)
- Produces: `SettingsService` class with `get()`, `update()`, `encrypt_secret()`, `decrypt_secret()`

- [ ] **Step 1: Write failing test for encryption round-trip**

```python
def test_dpapi_encrypt_decrypt_roundtrip():
    svc = SettingsService(session)
    plain = "my-secret-key"
    enc = svc.encrypt_secret(plain)
    assert enc != plain
    dec = svc.decrypt_secret(enc)
    assert dec == plain
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `SettingsService` using `win32crypt.CryptProtectData` / `CryptUnprotectData`**
- [ ] **Step 4: Implement `get()` (creates default row if missing) and `update(**kwargs)`**
- [ ] **Step 5: Run tests; verify encryption works on Windows**

---

### Task 4: Twitch OAuth Service

**Files:**
- Create: `apps/backend/src/services/twitch_service.py`
- Create: `apps/backend/tests/test_twitch_service.py`

**Interfaces:**
- Consumes: Task 3 (SettingsService for tokens)
- Produces: `TwitchService` with `get_auth_url()`, `exchange_code()`, `refresh_access_token()`, `get_vods()`, `get_vod_info()`, `download_vod()` (uses yt-dlp)

- [ ] **Step 1: Write failing test for auth URL generation**

```python
def test_auth_url_contains_required_params():
    url = twitch.get_auth_url()
    assert "client_id" in url
    assert "redirect_uri" in url
    assert "scope" in url
    assert "response_type=code" in url
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `TwitchService` with Helix API calls (httpx.AsyncClient)**
- [ ] **Step 4: Implement token refresh logic (auto-refresh on 401)**
- [ ] **Step 5: Implement `download_vod(vod_id, output_path)` using yt-dlp subprocess**
- [ ] **Step 6: Run tests with mocked httpx**

---

### Task 5: Whisper Transcription Worker

**Files:**
- Create: `apps/backend/src/workers/whisper_worker.py`
- Create: `apps/backend/src/schemas/whisper.py`
- Create: `apps/backend/tests/test_whisper_worker.py`
- Download: Whisper base.int8 model to `apps/backend/resources/models/whisper-base-int8/` (bundled)

**Interfaces:**
- Consumes: Task 2 (Job model), Settings (whisper_model, device, compute_type)
- Produces: `transcribe_audio(audio_path: str) -> TranscriptionResult` with `segments: List[Segment]`, `language: str`, `duration: float`

```python
class Segment(BaseModel):
    start: float
    end: float
    text: str
    words: List[Word]  # word-level timestamps

class Word(BaseModel):
    start: float
    end: float
    word: str
    probability: float
```

- [ ] **Step 1: Write failing test for transcription output structure**

```python
def test_transcribe_returns_segments_with_words():
    result = transcribe_audio("test_audio.wav")
    assert isinstance(result.segments, list)
    assert len(result.segments) > 0
    assert all(hasattr(s, 'words') for s in result.segments)
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `WhisperWorker` class using `faster_whisper.WhisperModel`**
  - Load model from bundled path (`resources/models/whisper-{model}-int8/`)
  - `compute_type="int8"`, `device="cpu"` (configurable)
  - `vad_filter=True` for streaming efficiency
  - Return word-level timestamps (`word_timestamps=True`)
- [ ] **Step 4: Add ARQ job `transcribe_job(ctx, job_id)` that updates Job progress**
- [ ] **Step 5: Run tests with sample audio file**

---

### Task 6: Gemini Viral Analysis Worker

**Files:**
- Create: `apps/backend/src/workers/gemini_worker.py`
- Create: `apps/backend/src/schemas/gemini.py`
- Create: `apps/backend/tests/test_gemini_worker.py`

**Interfaces:**
- Consumes: Task 5 (TranscriptionResult), Settings (gemini_api_key, virality_threshold)
- Produces: `analyze_viral(transcription: TranscriptionResult) -> ViralAnalysisResult`

```python
class ViralClip(BaseModel):
    start: float
    end: float
    score: float  # 0-1
    reason: str
    hook_title: str

class ViralAnalysisResult(BaseModel):
    clips: List[ViralClip]
    full_transcript: str
```

- [ ] **Step 1: Write failing test for analysis output structure**

```python
def test_analyze_returns_clips_with_scores():
    result = analyze_viral(mock_transcription)
    assert isinstance(result.clips, list)
    assert all(0 <= c.score <= 1 for c in result.clips)
    assert all(c.hook_title for c in result.clips)
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `GeminiWorker` with structured prompt:**
  - System prompt: "Você é um editor de clips virais para TikTok/Reels. Analise a transcrição e identifique os 3-5 melhores trechos de 15-60s que têm potencial viral. Considere: humor, surpresa, emoção, ensinamento, momento 'wtf'. Retorne JSON estrito."
  - User prompt: transcrição completa com timestamps
  - Model: `gemini-1.5-flash-latest`, `response_mime_type="application/json"`
  - Parse and validate JSON response
- [ ] **Step 4: Add ARQ job `analyze_viral_job(ctx, job_id, transcription_id)`**
- [ ] **Step 5: Run tests with mocked Gemini API**

---

### Task 7: FFmpeg Renderer (Vertical Crop + Face Tracking + Karaoke Subtitles)

**Files:**
- Create: `apps/backend/src/workers/render_worker.py`
- Create: `apps/backend/src/schemas/render.py`
- Create: `apps/backend/tests/test_render_worker.py`
- Download: YOLOv8n-face ONNX to `apps/backend/resources/models/yolov8n-face.onnx`

**Interfaces:**
- Consumes: Task 6 (ViralClip), source video path, Settings (subtitle_style, add_hook_titles)
- Produces: `render_clip(source: str, clip: ViralClip, transcription: TranscriptionResult, output: str) -> str` (output path)

- [ ] **Step 1: Write failing test for render output exists and is valid MP4**

```python
def test_render_creates_vertical_mp4():
    out = render_clip("source.mp4", viral_clip, transcription, "out.mp4")
    assert Path(out).exists()
    # probe with ffprobe: width=1080, height=1920
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement face detection with YOLOv8n ONNX (onnxruntime-directml)**
  - Detect faces per frame, track largest face, compute crop box (9:16) centered on face
  - Smooth crop trajectory (simple moving average over 15 frames)
- [ ] **Step 4: Implement karaoke subtitle rendering (ASS filter via FFmpeg)**
  - Generate `.ass` file from word-level timestamps
  - Style: `karaoke` = highlight word by word; `pop` = word pop-in; `minimal` = static line
  - Font: bundled `Montserrat-Bold.ttf`
- [ ] **Step 5: Implement hook title overlay (first 3s): bold text, outline, fade-in/out**
- [ ] **Step 6: FFmpeg command chain:**
  ```
  input → crop (face-track) → scale 1080x1920 → subtitles (ASS) → hook title (drawtext) → NVENC H.264 → output
  ```
  - Fallback to `libx264` if NVENC fails
- [ ] **Step 7: Add ARQ job `render_job(ctx, job_id, clip_ids)`**
- [ ] **Step 8: Run tests with sample video**

---

### Task 8: Job Orchestrator (ARQ Workers + Pipeline)

**Files:**
- Create: `apps/backend/src/workers/orchestrator.py`
- Create: `apps/backend/src/workers/__init__.py` (ARQ worker settings)
- Create: `apps/backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: Tasks 4-7 (all workers), Job model
- Produces: Pipeline functions `process_vod_job()`, `process_live_segment_job()` that chain: download → transcribe → analyze → render

- [ ] **Step 1: Write failing test for VOD pipeline creates Job with clips**

```python
@pytest.mark.asyncio
async def test_vod_pipeline_creates_clips():
    job_id = await enqueue_vod_job("https://twitch.tv/videos/123")
    await wait_for_job(job_id)
    job = get_job(job_id)
    assert job.status == "done"
    assert len(job.result_clips) > 0
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `process_vod_job(ctx, job_id)`:**
  1. Update job: "downloading" → yt-dlp download
  2. "transcribing" → segment audio (30s chunks) → transcribe each → merge
  3. "analyzing" → Gemini viral analysis
  4. "rendering" → for each viral clip: render
  5. "done" → save Clip rows, update Job
- [ ] **Step 4: Implement `process_live_segment_job(ctx, job_id, video_path, start_offset)`:**
  - Similar but skips download; processes last N minutes of live recording
- [ ] **Step 5: Configure ARQ `WorkerSettings` with all job functions, Redis connection**
- [ ] **Step 6: Run integration test with sample VOD (short)**

---

### Task 9: File Watcher (OBS Recordings Monitor)

**Files:**
- Create: `apps/backend/src/services/file_watcher.py`
- Create: `apps/backend/tests/test_file_watcher.py`

**Interfaces:**
- Consumes: Settings (obs_recordings_path, live_buffer_minutes, live_segment_seconds), Task 8 (enqueue_live_segment)
- Produces: `FileWatcher` class with `start()`, `stop()`, callback on new segment ready

- [ ] **Step 1: Write failing test for watcher detects new file**

```python
def test_watcher_triggers_on_stable_file(tmp_path):
    events = []
    watcher = FileWatcher(tmp_path, callback=lambda p: events.append(p))
    watcher.start()
    f = tmp_path / "test.mp4"
    f.write_bytes(b"x" * 1000)
    time.sleep(0.5)
    assert len(events) == 1
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `FileWatcher` using `watchdog.Observer`:**
  - Watch `obs_recordings_path` for `created`/`modified` events
  - Debounce: wait `live_buffer_minutes` after last modification before processing
  - Extract last `live_segment_seconds` from file (ffmpeg `-ss -t`)
  - Enqueue `process_live_segment_job` with segment path
  - Handle file rotation (OBS splits files every ~4GB or time)
- [ ] **Step 4: Add lifecycle management (start/stop, pause/resume)**
- [ ] **Step 5: Run tests with temp directory**

---

### Task 10: FastAPI REST API (Frontend ↔ Backend)

**Files:**
- Create: `apps/backend/src/api/__init__.py`
- Create: `apps/backend/src/api/routes/clips.py`
- Create: `apps/backend/src/api/routes/jobs.py`
- Create: `apps/backend/src/api/routes/settings.py`
- Create: `apps/backend/src/api/routes/twitch.py`
- Create: `apps/backend/src/api/routes/live.py`
- Create: `apps/backend/tests/test_api.py`

**Interfaces:**
- Consumes: Tasks 2-9 (all services)
- Produces: REST endpoints mounted at `/api/v1/`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/clips` | GET | List clips (pagination, filters: status, date) |
| `/clips/{id}` | GET | Clip details + download URL |
| `/clips/{id}/play` | GET | Stream video (Range requests) |
| `/jobs` | GET | List jobs |
| `/jobs` | POST | Create job (vod_url or live) |
| `/jobs/{id}` | GET | Job status + progress |
| `/settings` | GET | Current settings (secrets masked) |
| `/settings` | PATCH | Update settings |
| `/twitch/auth-url` | GET | OAuth URL |
| `/twitch/callback` | GET | OAuth callback (code exchange) |
| `/twitch/vods` | GET | List user VODs |
| `/live/status` | GET | Watcher status (running, paused, current file) |
| `/live/pause` | POST | Pause watcher |
| `/live/resume` | POST | Resume watcher |

- [ ] **Step 1: Write failing tests for each route (status codes, response shapes)**
- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement all routes with Pydantic request/response models**
- [ ] **Step 4: Add CORS middleware for Electron origin (`app://.`)**
- [ ] **Step 5: Run API tests with TestClient**

---

### Task 11: Electron Main Process (Backend Manager + IPC)

**Files:**
- Create: `apps/frontend/electron/main.ts`
- Create: `apps/frontend/electron/preload.ts`
- Create: `apps/frontend/electron/backend.ts`
- Create: `apps/frontend/src/types/electron.d.ts`

**Interfaces:**
- Consumes: Task 10 (API endpoints), backend binary path
- Produces: Electron `BrowserWindow`, `Tray`, IPC handlers, backend process manager

- [ ] **Step 1: Write `backend.ts` — manages Python backend subprocess:**
  - Dev: `uv run uvicorn src.main:app --port 8765`
  - Prod: `backend.exe` (bundled via extraResources)
  - Health check: poll `/api/v1/health` until ready
  - Graceful shutdown on app quit
- [ ] **Step 2: Write `preload.ts` — contextBridge for secure IPC:**
  - `api.getClips()`, `api.createJob()`, `api.getSettings()`, `api.updateSettings()`, `api.getTwitchAuthUrl()`, `api.onLiveStatus()`, etc.
- [ ] **Step 3: Write `main.ts` — window + tray + lifecycle:**
  - Main window: 1200x800, min 900x600, frameless? (no, standard)
  - Tray: icon, tooltip, menu (Open, Pause/Resume, Open Clips Folder, Quit)
  - Auto-launch backend on ready
  - Handle protocol `twitchclipper://callback` for OAuth
  - Auto-start registry (optional)
- [ ] **Step 4: Define TypeScript types for IPC in `electron.d.ts`**
- [ ] **Step 5: Run `npm run dev` — verify window opens, backend starts, API reachable**

---

### Task 12: React GUI — Layout, Routing, State

**Files:**
- Create: `apps/frontend/src/components/Layout.tsx`
- Create: `apps/frontend/src/components/Sidebar.tsx`
- Create: `apps/frontend/src/pages/Dashboard.tsx`
- Create: `apps/frontend/src/pages/Clips.tsx`
- Create: `apps/frontend/src/pages/Jobs.tsx`
- Create: `apps/frontend/src/pages/Settings.tsx`
- Create: `apps/frontend/src/pages/Live.tsx`
- Create: `apps/frontend/src/store/useAppStore.ts` (Zustand)
- Create: `apps/frontend/src/hooks/useApi.ts`
- Create: `apps/frontend/src/utils/format.ts`

**Interfaces:**
- Consumes: Task 11 (IPC/api), Task 10 (API shapes)
- Produces: Full GUI with 5 pages, global state, responsive layout

- [ ] **Step 1: Implement Zustand store with slices: `clips`, `jobs`, `settings`, `live`, `ui`**
- [ ] **Step 2: Implement `useApi` hook wrapping IPC calls with React Query-like caching**
- [ ] **Step 3: Build Layout: Sidebar (nav), Header (status, user), Main (pages)**
- [ ] **Step 4: Dashboard page — stats cards, recent clips, quick actions**
- [ ] **Step 5: Clips page — grid/list, player modal, filters, delete, open folder**
- [ ] **Step 6: Jobs page — table with progress bars, cancel, retry, logs**
- [ ] **Step 7: Live page — watcher status, current file, pause/resume, recent live clips**
- [ ] **Step 8: Settings page — forms for all Settings fields, validation, test buttons (Twitch, Gemini)**
- [ ] **Step 9: Run dev; verify all pages render, navigation works, state persists**

---

### Task 13: Video Player Component (Custom Controls)

**Files:**
- Create: `apps/frontend/src/components/VideoPlayer.tsx`
- Create: `apps/frontend/src/components/VideoPlayer.css`

**Interfaces:**
- Consumes: Clip object (output_path, duration)
- Produces: React component with play/pause, seek, volume, fullscreen, keyboard shortcuts

- [ ] **Step 1: Implement `<video>` wrapper with custom controls (Tailwind styled)**
- [ ] **Step 2: Support `file://` protocol for local MP4 (CORS not an issue)**
- [ ] **Step 3: Add keyboard: Space=play/pause, ArrowLeft/Right=seek ±5s, F=fullscreen, M=mute**
- [ ] **Step 4: Test with clips from `E:\clips\prontos\`**

---

### Task 14: First-Run Setup Wizard

**Files:**
- Create: `apps/frontend/src/pages/SetupWizard.tsx`
- Create: `apps/frontend/src/components/SetupStep.tsx`

**Interfaces:**
- Consumes: Task 12 (Settings page), Task 3 (SettingsService)
- Produces: Modal wizard on first launch (no settings in DB)

- [ ] **Step 1: Detect first run (Settings table empty or `gemini_api_key` missing)**
- [ ] **Step 2: Wizard steps:**
  1. Welcome + "Como funciona"
  2. Pastas (OBS recordings, saída clips) — valida existência
  3. Gemini API Key — link "Get free key" → aistudio.google.com, input + test
  4. Twitch (opcional) — Client ID/Secret ou "Pular"
  5. Modelo Whisper — selector (tiny/base/small) com aviso VRAM
  6. Conclusão — salva, inicia backend, abre Dashboard
- [ ] **Step 3: Persist settings via `api.updateSettings()`**
- [ ] **Step 4: Test fresh install (clear AppData folder)**

---

### Task 15: PyInstaller Backend Build

**Files:**
- Create: `apps/backend/twitch_clipper.spec`
- Create: `apps/backend/build_backend.py` (helper script)
- Modify: `apps/backend/pyproject.toml` (add `pyinstaller` config)

**Interfaces:**
- Consumes: Tasks 2-9 (all backend code), bundled resources (models, ffmpeg)
- Produces: `dist/backend.exe` (single file, ~150-200MB)

- [ ] **Step 1: Write `.spec` file with:**
  - `binaries`: ffmpeg.exe, YOLOv8n-face.onnx, Whisper model folder
  - `datas`: Montserrat font, any config templates
  - `hiddenimports`: faster_whisper, onnxruntime, google.generativeai, etc.
  - `exclude_module`: tests, pytest, jupyter, matplotlib, etc.
  - `upx`: True (compress)
- [ ] **Step 2: Write `build_backend.py` that copies resources to `dist/` structure**
- [ ] **Step 3: Run `pyinstaller twitch_clipper.spec` — verify `dist/backend.exe` runs standalone**
- [ ] **Step 4: Test backend.exe on clean Windows VM (no Python, no models)**

---

### Task 16: Electron Builder Packaging (NSIS Installer)

**Files:**
- Modify: `apps/frontend/package.json` (build config already in Task 1)
- Create: `apps/frontend/build/icon.ico`
- Create: `apps/frontend/build/installer.nsh` (custom NSIS script for auto-start registry)
- Create: `apps/frontend/release.js` (publish script placeholder)

**Interfaces:**
- Consumes: Task 11 (main.ts), Task 15 (backend.exe in extraResources)
- Produces: `dist_electron/Twitch Clipper Setup 0.1.0.exe`

- [ ] **Step 1: Verify `extraResources` includes `backend.exe` and `resources/` folder**
- [ ] **Step 2: Create `icon.ico` (256x256, 48x48, 32x32, 16x16)**
- [ ] **Step 3: Write `installer.nsh` for:**
  - Create `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` entry if auto_start enabled
  - Set uninstaller to remove registry key
- [ ] **Step 4: Run `npm run package` — verify installer builds**
- [ ] **Step 5: Install on clean VM; verify:**
  - App launches
  - Backend starts
  - GUI loads
  - Settings persist
  - System tray works
  - Auto-start toggle works

---

### Task 17: Integration Tests (Full Pipeline)

**Files:**
- Create: `apps/backend/tests/integration/test_full_pipeline.py`
- Create: `apps/frontend/tests/e2e/test_gui.cy.ts` (Cypress)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Automated verification of VOD → clips and live → clips flows

- [ ] **Step 1: Backend integration test:**
  - Use sample 2-min Twitch VOD (public, short)
  - Run `process_vod_job` end-to-end
  - Assert: clips created in output folder, DB rows, playable MP4
- [ ] **Step 2: Live simulation test:**
  - Write test MP4 to watched folder
  - Wait for watcher → job → clip
  - Assert: clip appears within `live_buffer_minutes + 60s`
- [ ] **Step 3: GUI E2E test (Cypress):**
  - Launch app, complete wizard
  - Navigate pages, verify data loads
  - Trigger VOD process, wait for clip, play in player

---

### Task 18: Documentation & Release Prep

**Files:**
- Create: `docs/USER_GUIDE.md`
- Create: `docs/DEVELOPER_GUIDE.md`
- Create: `CHANGELOG.md`
- Modify: `README.md` (badges, install instructions, screenshots)

**Interfaces:**
- Consumes: All tasks
- Produces: User-facing docs, dev onboarding

- [ ] **Step 1: Write USER_GUIDE.md — install, first run, wizard, OBS setup, using clips**
- [ ] **Step 2: Write DEVELOPER_GUIDE.md — architecture, adding workers, building, testing**
- [ ] **Step 3: Update README with screenshots, badges, quick start**
- [ ] **Step 4: Tag v0.1.0, create GitHub Release with installer**

---

## Execution Recommendation

**Plan complete and saved to `docs/superpowers/plans/2026-11-06-twitch-clipper-app.md`. Please review the plan. Which execution approach would you prefer?**

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end.

**For this plan I recommend Native, because the tasks are highly sequential (each depends on the previous's interfaces) and the monorepo structure means a single context can hold the whole design. A shipped mistake would cost a rebuild of the installer, but the plan's granular tests catch interface mismatches early. Does the plan capture what you want, and which approach should we use?**