/// <reference types="electron" />

interface Clip {
  id: number
  source_path: string
  source_type: string
  start: number
  end: number
  duration: number
  score: number
  reason: string
  output_path: string | null
  status: string
  created_at: string
}

interface Job {
  id: number
  type: string
  source_url: string | null
  source_path: string | null
  status: string
  progress: number
  current_step: string
  result_clips: number[]
  error: string | null
  created_at: string
}

interface Settings {
  obs_recordings_path: string
  clips_output_path: string
  temp_path: string
  twitch_client_id: string | null
  gemini_api_key: string | null
  whisper_model: string
  virality_threshold: number
  min_clip_duration: number
  max_clip_duration: number
  live_buffer_minutes: number
  live_segment_seconds: number
  add_hook_titles: boolean
  add_broll: boolean
  subtitle_style: string
  auto_start: boolean
}

interface LiveStatus {
  running: boolean
  paused: boolean
  current_file: string | null
  last_clip: string | null
}

interface ElectronAPI {
  // Clips
  getClips: (params?: { status?: string; limit?: number; offset?: number }) => Promise<{ clips: Clip[]; total: number }>
  getClip: (id: number) => Promise<Clip>
  playClip: (id: number) => string
  deleteClip: (id: number) => Promise<void>

  // Jobs
  getJobs: (params?: { status?: string; limit?: number; offset?: number }) => Promise<{ jobs: Job[]; total: number }>
  createJob: (job: { type: string; source_url?: string; source_path?: string }) => Promise<Job>
  getJob: (id: number) => Promise<Job>
  cancelJob: (id: number) => Promise<void>
  retryJob: (id: number) => Promise<void>

  // Settings
  getSettings: () => Promise<Settings>
  updateSettings: (settings: Partial<Settings>) => Promise<Settings>
  testTwitch: () => Promise<{ status: string; message: string }>
  testGemini: () => Promise<{ status: string; message: string }>

  // Twitch
  getTwitchAuthUrl: () => Promise<{ auth_url: string }>
  getVods: () => Promise<Array<{ id: string; title: string; url: string; created_at: string; duration: string; view_count: number }>>

  // Live
  getLiveStatus: () => Promise<LiveStatus>
  pauseLive: () => Promise<void>
  resumeLive: () => Promise<void>
  startLive: () => Promise<void>
  stopLive: () => Promise<void>

  // App
  openFolder: (path: string) => Promise<void>
  openExternal: (url: string) => Promise<void>
}

interface ElectronEvents {
  onLiveStatus: (callback: (status: LiveStatus) => void) => () => void
  onJobUpdate: (callback: (job: Job) => void) => () => void
  onClipCreated: (callback: (clip: Clip) => void) => () => void
  onOAuthCallback: (callback: (code: string) => void) => () => void
}

interface ElectronAppInfo {
  version: string
  platform: string
}

declare global {
  interface Window {
    api: ElectronAPI
    events: ElectronEvents
    appInfo: ElectronAppInfo
  }
}

export {}