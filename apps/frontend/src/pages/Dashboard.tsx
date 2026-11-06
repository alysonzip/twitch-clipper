import { Video, Clock, CheckCircle, AlertTriangle, ExternalLink } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

export default function Dashboard() {
  const { clips, jobs, liveStatus } = useAppStore()

  const stats = [
    { label: 'Total de Clips', value: clips.length, icon: Video, color: 'text-purple-600 bg-purple-100' },
    { label: 'Clips Prontos', value: clips.filter(c => c.status === 'done').length, icon: CheckCircle, color: 'text-green-600 bg-green-100' },
    { label: 'Jobs Ativos', value: jobs.filter(j => ['queued', 'processing'].includes(j.status)).length, icon: Clock, color: 'text-blue-600 bg-blue-100' },
    { label: 'Status Live', value: liveStatus.running ? (liveStatus.paused ? 'Pausado' : 'Rodando') : 'Parado', icon: AlertTriangle, color: liveStatus.running ? (liveStatus.paused ? 'text-yellow-600 bg-yellow-100' : 'text-green-600 bg-green-100') : 'text-slate-600 bg-slate-100' },
  ]

  const recentClips = clips.slice(-5).reverse()
  const recentJobs = jobs.slice(-5).reverse()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Clips Recentes</h3>
            <a href="#" className="text-sm text-purple-600 hover:underline flex items-center gap-1">
              Ver todos <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          {recentClips.length === 0 ? (
            <p className="text-slate-500 text-center py-8">Nenhum clip ainda. Processe um VOD ou inicie a live.</p>
          ) : (
            <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin">
              {recentClips.map((clip) => (
                <div key={clip.id} className="flex items-center gap-3 p-2 hover:bg-slate-50 rounded-lg">
                  <div className="w-16 h-9 bg-slate-100 rounded flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{clip.sourcePath.split('\\').pop() || 'Clip'}</p>
                    <p className="text-xs text-slate-500">{clip.duration.toFixed(1)}s • Score: {clip.score.toFixed(2)}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    clip.status === 'done' ? 'bg-green-100 text-green-700' :
                    clip.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    'bg-red-100 text-red-700'
                  }`}>{clip.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Jobs Recentes</h3>
            <a href="#" className="text-sm text-purple-600 hover:underline flex items-center gap-1">
              Ver todos <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          {recentJobs.length === 0 ? (
            <p className="text-slate-500 text-center py-8">Nenhum job ainda.</p>
          ) : (
            <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center gap-3 p-2 hover:bg-slate-50 rounded-lg">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-slate-100">
                    {job.type === 'vod' ? '📺' : '🔴'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{job.type === 'vod' ? 'VOD' : 'Live'} • {job.currentStep || 'Na fila'}</p>
                    <div className="w-full h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden">
                      <div className="h-full bg-purple-600 rounded-full transition-all" style={{ width: `${job.progress}%` }} />
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    job.status === 'done' ? 'bg-green-100 text-green-700' :
                    job.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    job.status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-slate-100 text-slate-700'
                  }`}>{job.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Ações Rápidas</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <button className="p-4 border-2 border-dashed border-slate-300 rounded-xl hover:border-purple-400 hover:bg-purple-50 transition-colors text-left">
            <Video className="w-8 h-8 text-purple-600 mb-2" />
            <p className="font-medium text-slate-900">Processar VOD</p>
            <p className="text-sm text-slate-500">Colar URL da Twitch</p>
          </button>
          <button className="p-4 border-2 border-dashed border-slate-300 rounded-xl hover:border-green-400 hover:bg-green-50 transition-colors text-left">
            <CheckCircle className="w-8 h-8 text-green-600 mb-2" />
            <p className="font-medium text-slate-900">Iniciar Monitoramento Live</p>
            <p className="text-sm text-slate-500">Observar pasta OBS</p>
          </button>
          <button className="p-4 border-2 border-dashed border-slate-300 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-colors text-left">
            <ExternalLink className="w-8 h-8 text-blue-600 mb-2" />
            <p className="font-medium text-slate-900">Abrir Pasta de Clips</p>
            <p className="text-sm text-slate-500">E:\\clips\\prontos</p>
          </button>
        </div>
      </div>
    </div>
  )
}