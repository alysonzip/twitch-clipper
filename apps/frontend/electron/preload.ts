import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron'

// Type definitions for the exposed API
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

interface ApiResponse<T> {
  data?: T
  error?: string
}

// Helper to call backend API
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`http://localhost:8765${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Expose API to renderer process
contextBridge.exposeInMainWorld('api', {
  // Clips
  getClips: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams()
    if (params?.status) query.set('status', params.status)
    if (params?.limit) query.set('limit', params.limit.toString())
    if (params?.offset) query.set('offset', params.offset.toString())
    return apiCall<{ clips: Clip[]; total: number }>(`/api/v1/clips?${query}`)
  },

  getClip: (id: number) => apiCall<Clip>(`/api/v1/clips/${id}`),

  playClip: (id: number) => `http://localhost:8765/api/v1/clips/${id}/play`,

  deleteClip: (id: number) => apiCall<void>(`/api/v1/clips/${id}`, { method: 'DELETE' }),

  // Jobs
  getJobs: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams()
    if (params?.status) query.set('status', params.status)
    if (params?.limit) query.set('limit', params.limit.toString())
    if (params?.offset) query.set('offset', params.offset.toString())
    return apiCall<{ jobs: Job[]; total: number }>(`/api/v1/jobs?${query}`)
  },

  createJob: (job: { type: string; source_url?: string; source_path?: string }) =>
    apiCall<Job>('/api/v1/jobs', {
      method: 'POST',
      body: JSON.stringify(job),
    }),

  getJob: (id: number) => apiCall<Job>(`/api/v1/jobs/${id}`),

  cancelJob: (id: number) => apiCall<void>(`/api/v1/jobs/${id}/cancel`, { method: 'POST' }),

  retryJob: (id: number) => apiCall<void>(`/api/v1/jobs/${id}/retry`, { method: 'POST' }),

  // Settings
  getSettings: () => apiCall<Settings>('/api/v1/settings'),

  updateSettings: (settings: Partial<Settings>) =>
    apiCall<Settings>('/api/v1/settings', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    }),

  testTwitch: () => apiCall<{ status: string; message: string }>('/api/v1/settings/test/twitch', { method: 'POST' }),

  testGemini: () => apiCall<{ status: string; message: string }>('/api/v1/settings/test/gemini', { method: 'POST' }),

  // Twitch
  getTwitchAuthUrl: () => apiCall<{ auth_url: string }>('/api/v1/twitch/auth-url'),

  getVods: () => apiCall<Array<{ id: string; title: string; url: string; created_at: string; duration: string; view_count: number }>>('/api/v1/twitch/vods'),

  // Live
  getLiveStatus: () => apiCall<LiveStatus>('/api/v1/live/status'),

  pauseLive: () => apiCall<void>('/api/v1/live/pause', { method: 'POST' }),

  resumeLive: () => apiCall<void>('/api/v1/live/resume', { method: 'POST' }),

  startLive: () => apiCall<void>('/api/v1/live/start', { method: 'POST' }),

  stopLive: () => apiCall<void>('/api/v1/live/stop', { method: 'POST' }),

  // App
  openFolder: (path: string) => ipcRenderer.invoke('app:open-folder', path),

  openExternal: (url: string) => ipcRenderer.invoke('app:open-external', url),
})

// Expose event listeners
contextBridge.exposeInMainWorld('events', {
  onLiveStatus: (callback: (status: LiveStatus) => void) => {
    const handler = (_: IpcRendererEvent, status: LiveStatus) => callback(status)
    ipcRenderer.on('live:status', handler)
    return () => ipcRenderer.off('live:status', handler)
  },

  onJobUpdate: (callback: (job: Job) => void) => {
    const handler = (_: IpcRendererEvent, job: Job) => callback(job)
    ipcRenderer.on('job:update', handler)
    return () => ipcRenderer.off('job:update', handler)
  },

  onClipCreated: (callback: (clip: Clip) => void) => {
    const handler = (_: IpcRendererEvent, clip: Clip) => callback(clip)
    ipcRenderer.on('clip:created', handler)
    return () => ipcRenderer.off('clip:created', handler)
  },

  onOAuthCallback: (callback: (code: string) => void) => {
    const handler = (_: IpcRendererEvent, code: string) => callback(code)
    ipcRenderer.on('oauth:callback', handler)
    return () => ipcRenderer.off('oauth:callback', handler)
  },
})

// Expose app info
contextBridge.exposeInMainWorld('appInfo', {
  version: process.env.npm_package_version || '0.1.0',
  platform: process.platform,
})