import { Save, TestTube, Key, FolderOpen, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'

type Field = {
  key: string
  label: string
  type: 'text' | 'password' | 'number' | 'select' | 'boolean'
  placeholder?: string
  step?: number
  min?: number
  max?: number
  options?: { value: string; label: string }[]
}

type Section = {
  title: string
  icon: LucideIcon
  fields: Field[]
  test?: string
  help?: string
}

export default function Settings() {
  const { settings, setSettings, setSettingsLoaded } = useAppStore()
  const [testResults, setTestResults] = useState<Record<string, { status: 'success' | 'error' | 'testing'; message: string }>>({})
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      // In real implementation, call backend API to save settings
      // await fetch('/api/v1/settings', { method: 'PATCH', body: JSON.stringify(settings) })
      setSettingsLoaded(true)
      setTestResults({})
    } catch (e) {
      console.error('Failed to save settings', e)
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (type: string) => {
    setTestResults(prev => ({ ...prev, [type]: { status: 'testing', message: 'Testando...' }}))
    try {
      // In real implementation, call backend API to test connection
      // await fetch(`/api/v1/settings/test/${type}`, { method: 'POST' })
      await new Promise(r => setTimeout(r, 1000))
      setTestResults(prev => ({ ...prev, [type]: { status: 'success', message: 'Conexão OK!' }}))
    } catch (e) {
      setTestResults(prev => ({ ...prev, [type]: { status: 'error', message: 'Falha na conexão' }}))
    }
  }

  const sections: Section[] = [
    {
      title: 'Pastas',
      icon: FolderOpen,
      fields: [
        { key: 'obsRecordingsPath', label: 'Pasta de Gravações do OBS', type: 'text', placeholder: 'E:\\OBS\\Recordings' },
        { key: 'clipsOutputPath', label: 'Pasta de Saída dos Clips', type: 'text', placeholder: 'E:\\clips\\prontos' },
        { key: 'tempPath', label: 'Pasta Temporária', type: 'text', placeholder: 'E:\\clips\\processando' },
      ],
    },
    {
      title: 'Twitch',
      icon: TestTube,
      fields: [
        { key: 'twitchClientId', label: 'Client ID', type: 'text', placeholder: 'Seu Twitch Client ID' },
        // Client Secret would be handled securely via backend
      ],
      test: 'twitch',
    },
    {
      title: 'IA (Gemini)',
      icon: Key,
      fields: [
        { key: 'geminiApiKey', label: 'Gemini API Key', type: 'password', placeholder: 'Cole sua chave do Google AI Studio' },
      ],
      test: 'gemini',
      help: 'Obtenha grátis em <a href="https://aistudio.google.com" target="_blank" rel="noopener" className="text-purple-600 hover:underline">aistudio.google.com</a> (1500 req/dia grátis)',
    },
    {
      title: 'Whisper (Transcrição Local)',
      icon: TestTube,
      fields: [
        { key: 'whisperModel', label: 'Modelo', type: 'select', options: [
          { value: 'tiny', label: 'Tiny (mais rápido, menos preciso)' },
          { value: 'base', label: 'Base (recomendado para RX 550)' },
          { value: 'small', label: 'Small (mais lento, melhor qualidade)' },
        ]},
      ],
      help: 'Modelos maiores precisam de mais VRAM. Com RX 550 4GB, "base" é o ideal.',
    },
    {
      title: 'Corte & Viral',
      icon: TestTube,
      fields: [
        { key: 'viralityThreshold', label: 'Threshold Viral (0-1)', type: 'number', step: 0.01, min: 0.5, max: 0.99 },
        { key: 'minClipDuration', label: 'Duração Mínima (s)', type: 'number', min: 5, max: 60 },
        { key: 'maxClipDuration', label: 'Duração Máxima (s)', type: 'number', min: 15, max: 120 },
        { key: 'liveBufferMinutes', label: 'Buffer Live (min)', type: 'number', min: 1, max: 10 },
        { key: 'liveSegmentSeconds', label: 'Segmento Live (s)', type: 'number', min: 15, max: 120 },
      ],
    },
    {
      title: 'Estilo dos Clips',
      icon: TestTube,
      fields: [
        { key: 'addHookTitles', label: 'Adicionar Títulos Hook', type: 'boolean' },
        { key: 'addBroll', label: 'Adicionar B-Roll (Pexels)', type: 'boolean' },
        { key: 'subtitleStyle', label: 'Estilo Legendas', type: 'select', options: [
          { value: 'karaoke', label: 'Karaoke (palavra por palavra)' },
          { value: 'pop', label: 'Pop (aparece palavra)' },
          { value: 'minimal', label: 'Minimal (linha estática)' },
        ]},
      ],
    },
    {
      title: 'Geral',
      icon: TestTube,
      fields: [
        { key: 'autoStart', label: 'Iniciar com Windows', type: 'boolean' },
      ],
    },
  ]

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Configurações</h2>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Salvando...' : 'Salvar Configurações'}
        </button>
      </div>

      {sections.map((section) => {
        const test = section.test
        return (
        <div key={section.title} className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <section.icon className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-slate-900">{section.title}</h3>
            {test && (
              <button
                onClick={() => testConnection(test)}
                disabled={testResults[test]?.status === 'testing'}
                className="ml-auto px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 transition-colors"
              >
                {testResults[test]?.status === 'testing' ? (
                  <> <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> Testando... </>
                ) : testResults[test]?.status === 'success' ? (
                  <> <CheckCircle className="w-3 h-3 inline text-green-600 mr-1" /> OK </>
                ) : testResults[test]?.status === 'error' ? (
                  <> <AlertCircle className="w-3 h-3 inline text-red-600 mr-1" /> Falhou </>
                ) : (
                  'Testar'
                )}
              </button>
            )}
          </div>

          {section.help && (
            <p className="text-sm text-slate-500 mb-4" dangerouslySetInnerHTML={{ __html: section.help }} />
          )}

          <div className="space-y-4">
            {section.fields.map((field) => (
              <div key={field.key} className="space-y-1">
                <label className="block text-sm font-medium text-slate-700">{field.label}</label>
                {field.type === 'text' && (
                  <input
                    type="text"
                    value={settings[field.key as keyof typeof settings] as string}
                    onChange={(e) => setSettings({ [field.key]: e.target.value })}
                    placeholder={field.placeholder}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                )}
                {field.type === 'password' && (
                  <input
                    type="password"
                    value={settings[field.key as keyof typeof settings] as string}
                    onChange={(e) => setSettings({ [field.key]: e.target.value })}
                    placeholder={field.placeholder}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                )}
                {field.type === 'number' && (
                  <input
                    type="number"
                    value={settings[field.key as keyof typeof settings] as number}
                    onChange={(e) => setSettings({ [field.key]: parseFloat(e.target.value) || 0 })}
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    className="w-full max-w-xs px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                )}
                {field.type === 'select' && (
                  <select
                    value={settings[field.key as keyof typeof settings] as string}
                    onChange={(e) => setSettings({ [field.key]: e.target.value })}
                    className="w-full max-w-xs px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {field.options?.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}
                {field.type === 'boolean' && (
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings[field.key as keyof typeof settings] as boolean}
                      onChange={(e) => setSettings({ [field.key]: e.target.checked })}
                      className="w-4 h-4 text-purple-600 border-slate-300 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm text-slate-700">Ativado</span>
                  </label>
                )}
              </div>
            ))}
          </div>
        </div>
        )
      })}

      <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-900 mb-3">Sobre</h3>
        <div className="text-sm text-slate-600 space-y-1">
          <p><strong>Twitch Clipper</strong> v0.1.0</p>
          <p>App standalone para criar clips virais de lives da Twitch</p>
          <p>Whisper local (CPU) + Gemini Flash (nuvem) + FFmpeg (NVENC)</p>
          <p className="mt-2">
            <a href="https://github.com" target="_blank" rel="noopener" className="text-purple-600 hover:underline">GitHub</a> •
            <a href="https://supoclip.com" target="_blank" rel="noopener" className="text-purple-600 hover:underline">SupoClip</a>
          </p>
        </div>
      </div>
    </div>
  )
}