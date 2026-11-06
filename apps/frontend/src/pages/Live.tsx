import { PlayCircle, PauseCircle, FolderOpen, RefreshCw, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { useEffect } from 'react'

export default function Live() {
  const { liveStatus, setLiveStatus, settings } = useAppStore()

  useEffect(() => {
    // Simulate fetching live status from backend
    const fetchStatus = async () => {
      try {
        // In real implementation, this would call the backend API
        // const res = await fetch('/api/v1/live/status')
        // const data = await res.json()
        // setLiveStatus(data)
      } catch (e) {
        console.error('Failed to fetch live status', e)
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [setLiveStatus])

  const handleStart = () => {
    setLiveStatus({ running: true, paused: false })
    // Call backend API to start watcher
  }

  const handlePause = () => {
    setLiveStatus({ paused: true })
    // Call backend API to pause watcher
  }

  const handleResume = () => {
    setLiveStatus({ paused: false })
    // Call backend API to resume watcher
  }

  const handleStop = () => {
    setLiveStatus({ running: false, paused: false, currentFile: null })
    // Call backend API to stop watcher
  }

  const handleOpenFolder = () => {
    // Open clips output folder
    window.api?.openFolder?.(settings.clipsOutputPath)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Monitoramento Ao Vivo</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenFolder}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2 text-sm"
          >
            <FolderOpen className="w-4 h-4" />
            Abrir Pasta de Clips
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-medium text-slate-500 mb-2">Status do Monitoramento</h3>
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              liveStatus.running ? (liveStatus.paused ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600') : 'bg-slate-100 text-slate-400'
            }`}>
              {liveStatus.running ? (liveStatus.paused ? <PauseCircle className="w-6 h-6" /> : <PlayCircle className="w-6 h-6" />) : <AlertTriangle className="w-6 h-6" />}
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">
                {liveStatus.running ? (liveStatus.paused ? 'Pausado' : 'Rodando') : 'Parado'}
              </p>
              <p className="text-sm text-slate-500">
                {liveStatus.paused ? 'Aguardando retomada' : liveStatus.running ? 'Monitorando pasta OBS' : 'Clique em Iniciar para começar'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-medium text-slate-500 mb-2">Arquivo Atual</h3>
          <p className="font-mono text-sm text-slate-900 truncate max-w-xs" title={liveStatus.currentFile || ''}>
            {liveStatus.currentFile || 'Nenhum arquivo detectado'}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-medium text-slate-500 mb-2">Último Clip Gerado</h3>
          <p className="font-mono text-sm text-slate-900 truncate max-w-xs" title={liveStatus.lastClip || ''}>
            {liveStatus.lastClip || 'Nenhum ainda'}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Controles</h3>
        <div className="flex flex-wrap gap-3">
          {!liveStatus.running && (
            <button
              onClick={handleStart}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 font-medium"
            >
              <PlayCircle className="w-5 h-5" />
              Iniciar Monitoramento
            </button>
          )}
          {liveStatus.running && !liveStatus.paused && (
            <button
              onClick={handlePause}
              className="px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center gap-2 font-medium"
            >
              <PauseCircle className="w-5 h-5" />
              Pausar
            </button>
          )}
          {liveStatus.running && liveStatus.paused && (
            <button
              onClick={handleResume}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium"
            >
              <PlayCircle className="w-5 h-5" />
              Retomar
            </button>
          )}
          {liveStatus.running && (
            <button
              onClick={handleStop}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 font-medium"
            >
              <AlertTriangle className="w-5 h-5" />
              Parar
            </button>
          )}
          <button
            onClick={handleOpenFolder}
            className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2 font-medium"
          >
            <FolderOpen className="w-5 h-5" />
            Abrir Pasta de Clips
          </button>
          <button
            onClick={() => { /* refresh status */ }}
            className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2 font-medium"
          >
            <RefreshCw className="w-5 h-5" />
            Atualizar Status
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Como funciona</h3>
        <div className="grid gap-4 sm:grid-cols-3 text-sm">
          <div className="p-4 bg-slate-50 rounded-lg">
            <Loader2 className="w-6 h-6 text-purple-600 mb-2" />
            <h4 className="font-medium text-slate-900 mb-1">1. OBS Grava</h4>
            <p className="text-slate-500">Configure OBS para gravar em <code className="bg-slate-100 px-1 rounded">{settings.obsRecordingsPath}</code></p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <CheckCircle className="w-6 h-6 text-green-600 mb-2" />
            <h4 className="font-medium text-slate-900 mb-1">2. App Detecta</h4>
            <p className="text-slate-500">File watcher monitora a pasta e pega os últimos {settings.liveSegmentSeconds}s a cada {settings.liveBufferMinutes}min</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <PlayCircle className="w-6 h-6 text-blue-600 mb-2" />
            <h4 className="font-medium text-slate-900 mb-1">3. IA Processa</h4>
            <p className="text-slate-500">Whisper transcreve → Gemini analisa → FFmpeg corta vertical 9:16 com legendas karaoke</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Configuração do OBS</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <span className="text-slate-700">Settings → Output → Recording → Recording Path: <code className="bg-slate-100 px-1 rounded">{settings.obsRecordingsPath}</code></span>
          </div>
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <span className="text-slate-700">Recording Format: <strong>MP4</strong> (não MKV/FLV)</span>
          </div>
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <span className="text-slate-700">Encoder: <strong>NVENC H.264</strong> (usa GPU, mais rápido)</span>
          </div>
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <span className="text-slate-700">Keyframe Interval: <strong>2s</strong> (para cortes precisos)</span>
          </div>
        </div>
      </div>
    </div>
  )
}