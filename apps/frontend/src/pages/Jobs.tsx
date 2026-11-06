import { RotateCcw, XCircle, Eye, Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

export default function Jobs() {
  const { jobs } = useAppStore()

  const statusColors = {
    queued: 'bg-slate-100 text-slate-700',
    processing: 'bg-blue-100 text-blue-700',
    done: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }

  const statusIcons = {
    queued: Clock,
    processing: Loader2,
    done: CheckCircle,
    failed: AlertCircle,
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Jobs</h2>

      {jobs.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Loader2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Nenhum job ainda</p>
          <p className="text-sm text-slate-400 mt-1">Processe um VOD ou inicie o monitoramento live para criar jobs</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Origem</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Progresso</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Etapa Atual</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Clips</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Criado</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider pr-4">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {jobs.slice().reverse().map((job) => {
                  const StatusIcon = statusIcons[job.status as keyof typeof statusIcons] || Clock
                  return (
                  <tr key={job.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${job.type === 'vod' ? 'bg-purple-100 text-purple-700' : 'bg-red-100 text-red-700'}`}>
                        {job.type === 'vod' ? 'VOD' : 'Live'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-900 truncate max-w-xs" title={job.sourceUrl || job.sourcePath || ''}>
                      {job.sourceUrl || job.sourcePath || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${statusColors[job.status as keyof typeof statusColors] || 'bg-slate-100 text-slate-700'}`}>
                        <StatusIcon className="w-3 h-3 inline mr-1" />
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-purple-600 rounded-full transition-all" style={{ width: `${job.progress}%` }} />
                      </div>
                      <span className="text-xs text-slate-500 ml-1">{job.progress}%</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 max-w-md truncate" title={job.currentStep}>
                      {job.currentStep || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-900">{job.resultClips.length}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">
                      {new Date(job.createdAt).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-3 text-right pr-4">
                      <div className="flex items-center justify-end gap-2">
                        {job.status === 'processing' && (
                          <button className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Cancelar">
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                        {(job.status === 'failed' || job.status === 'done') && (
                          <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Tentar novamente">
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                        {job.resultClips.length > 0 && (
                          <button className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg" title="Ver clips">
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}