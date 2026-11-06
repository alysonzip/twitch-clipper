import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Settings {
  obsRecordingsPath: string
  clipsOutputPath: string
  tempPath: string
  twitchClientId: string
  geminiApiKey: string
  whisperModel: string
  viralityThreshold: number
  minClipDuration: number
  maxClipDuration: number
  liveBufferMinutes: number
  liveSegmentSeconds: number
  addHookTitles: boolean
  addBroll: boolean
  subtitleStyle: string
  autoStart: boolean
}

interface Clip {
  id: number
  sourcePath: string
  sourceType: string
  start: number
  end: number
  duration: number
  score: number
  reason: string
  outputPath: string | null
  status: string
  createdAt: string
}

interface Job {
  id: number
  type: string
  sourceUrl: string | null
  sourcePath: string | null
  status: string
  progress: number
  currentStep: string
  resultClips: number[]
  error: string | null
  createdAt: string
}

interface LiveStatus {
  running: boolean
  paused: boolean
  currentFile: string | null
  lastClip: string | null
}

interface AppState {
  isSidebarOpen: boolean
  toggleSidebar: () => void
  settingsLoaded: boolean
  setSettingsLoaded: (loaded: boolean) => void
  isFirstRun: boolean
  setIsFirstRun: (firstRun: boolean) => void
  settings: Settings
  setSettings: (settings: Partial<Settings>) => void
  clips: Clip[]
  setClips: (clips: Clip[]) => void
  jobs: Job[]
  setJobs: (jobs: Job[]) => void
  liveStatus: LiveStatus
  setLiveStatus: (status: Partial<LiveStatus>) => void
}

const defaultSettings: Settings = {
  obsRecordingsPath: 'E:\\OBS\\Recordings',
  clipsOutputPath: 'E:\\clips\\prontos',
  tempPath: 'E:\\clips\\processando',
  twitchClientId: '',
  geminiApiKey: '',
  whisperModel: 'base',
  viralityThreshold: 0.85,
  minClipDuration: 15,
  maxClipDuration: 60,
  liveBufferMinutes: 2,
  liveSegmentSeconds: 30,
  addHookTitles: true,
  addBroll: false,
  subtitleStyle: 'karaoke',
  autoStart: false,
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      settingsLoaded: true,
      setSettingsLoaded: (loaded) => set({ settingsLoaded: loaded }),
      isFirstRun: true,
      setIsFirstRun: (firstRun) => set({ isFirstRun: firstRun }),
      settings: defaultSettings,
      setSettings: (newSettings) => set((state) => ({ settings: { ...state.settings, ...newSettings } })),
      clips: [],
      setClips: (clips) => set({ clips }),
      jobs: [],
      setJobs: (jobs) => set({ jobs }),
      liveStatus: { running: false, paused: false, currentFile: null, lastClip: null },
      setLiveStatus: (status) => set((state) => ({ liveStatus: { ...state.liveStatus, ...status } })),
    }),
    {
      name: 'twitch-clipper-store',
      partialize: (state) => ({
        isSidebarOpen: state.isSidebarOpen,
        settings: state.settings,
        isFirstRun: state.isFirstRun,
      }),
    }
  )
)