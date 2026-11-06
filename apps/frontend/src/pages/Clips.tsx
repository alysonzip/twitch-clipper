import { Search, Video, Play, Trash2, FolderOpen, MoreHorizontal } from 'lucide-react'
import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import VideoPlayer from '../components/VideoPlayer'

export default function Clips() {
  const { clips } = useAppStore()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'done' | 'processing' | 'failed'>('all')
  const [selectedClip, setSelectedClip] = useState<any>(null)

  const filteredClips = clips
    .filter(c => statusFilter === 'all' || c.status === statusFilter)
    .filter(c => c.sourcePath.toLowerCase().includes(search.toLowerCase()) || c.reason.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-2xl font-bold text-slate-900">Clips</h2>
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar clips..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="all">Todos</option>
            <option value="done">Prontos</option>
            <option value="processing">Processando</option>
            <option value="failed">Falhou</option>
          </select>
        </div>
      </div>

      {filteredClips.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Video className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Nenhum clip encontrado</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredClips.map((clip) => (
            <div key={clip.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="relative aspect-[16/9] bg-slate-100">
                {clip.status === 'done' && clip.outputPath && (
                  <VideoPlayer
                    src={`file://${clip.outputPath}`}
                    poster=""
                    onClick={() => setSelectedClip(clip)}
                  />
                )}
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => { e.stopPropagation(); setSelectedClip(clip); }}
                    className="p-3 bg-white rounded-full shadow-lg hover:bg-slate-100 transition-colors"
                  >
                    <Play className="w-6 h-6 text-slate-900" />
                  </button>
                </div>
                <div className="absolute top-2 right-2 flex gap-1">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    clip.status === 'done' ? 'bg-green-100 text-green-700' :
                    clip.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    'bg-red-100 text-red-700'
                  }`}>{clip.status}</span>
                </div>
              </div>
              <div className="p-3 space-y-2">
                <p className="text-sm font-medium text-slate-900 truncate" title={clip.sourcePath.split('\\').pop() || 'Clip'}>
                  {clip.sourcePath.split('\\').pop() || 'Clip'}
                </p>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{clip.duration.toFixed(1)}s</span>
                  <span>Score: {clip.score.toFixed(2)}</span>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2">{clip.reason}</p>
                <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                  <button className="flex-1 py-1.5 text-xs font-medium text-slate-700 hover:text-purple-600" onClick={(e) => { e.stopPropagation(); setSelectedClip(clip); }}>
                    <Play className="w-3 h-3 inline mr-1" /> Play
                  </button>
                  <button className="p-1.5 text-slate-400 hover:text-slate-600" title="Abrir pasta">
                    <FolderOpen className="w-4 h-4" />
                  </button>
                  <button className="p-1.5 text-slate-400 hover:text-red-600" title="Excluir">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedClip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={() => setSelectedClip(null)}>
          <div className="bg-white rounded-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">{selectedClip.sourcePath.split('\\').pop() || 'Clip'}</h3>
              <button onClick={() => setSelectedClip(null)} className="p-1 text-slate-400 hover:text-slate-600">
                <MoreHorizontal className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4" style={{ maxHeight: '70vh', overflow: 'auto' }}>
              <VideoPlayer src={`file://${selectedClip.outputPath}`} />
              <div className="mt-4 space-y-2 text-sm">
                <p><strong>Duração:</strong> {selectedClip.duration.toFixed(1)}s</p>
                <p><strong>Score viral:</strong> {selectedClip.score.toFixed(2)}</p>
                <p><strong>Motivo:</strong> {selectedClip.reason}</p>
                <p><strong>Intervalo:</strong> {selectedClip.start.toFixed(1)}s - {selectedClip.end.toFixed(1)}s</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}