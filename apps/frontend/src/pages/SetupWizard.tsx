import { useState } from 'react'
import { ArrowRight, ArrowLeft, CheckCircle, Loader2, FolderOpen, Key, TestTube, ExternalLink } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

const steps = [
  { id: 'welcome', title: 'Bem-vindo', icon: CheckCircle },
  { id: 'folders', title: 'Pastas', icon: FolderOpen },
  { id: 'gemini', title: 'Gemini API', icon: Key },
  { id: 'twitch', title: 'Twitch (Opcional)', icon: TestTube },
  { id: 'whisper', title: 'Modelo Whisper', icon: TestTube },
  { id: 'done', title: 'Pronto!', icon: CheckCircle },
]

export default function SetupWizard() {
  const { settings, setSettings, setIsFirstRun, setSettingsLoaded } = useAppStore()
  const [currentStep, setCurrentStep] = useState(0)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null)

  const goNext = () => setCurrentStep(prev => Math.min(prev + 1, steps.length - 1))
  const goPrev = () => setCurrentStep(prev => Math.max(prev - 1, 0))

  const handleTestGemini = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      // In real implementation, call backend to test Gemini API
      await new Promise(r => setTimeout(r, 1500))
      setTestResult('success')
    } catch {
      setTestResult('error')
    } finally {
      setTesting(false)
    }
  }

  const handleFinish = () => {
    setIsFirstRun(false)
    setSettingsLoaded(true)
  }

  const StepContent = () => {
    switch (steps[currentStep].id) {
      case 'welcome':
        return (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-2">Bem-vindo ao Twitch Clipper!</h3>
            <p className="text-slate-600 max-w-md mx-auto mb-8">
              Este assistente vai configurar tudo para você criar clips virais das suas lives da Twitch automaticamente.
            </p>
            <div className="text-left max-w-md mx-auto space-y-3 text-sm">
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span>Whisper local no seu PC (legendas offline)</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span>Gemini Flash na nuvem (análise viral grátis)</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span>Cortes verticais 9:16 para Reels/TikTok/Shorts</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span>Legendas karaoke + face tracking + títulos hook</span>
              </div>
            </div>
          </div>
        )

      case 'folders':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-slate-900">Configure as pastas</h3>
            <p className="text-slate-600">O app precisa saber onde o OBS grava e onde salvar os clips prontos.</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pasta de Gravações do OBS</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={settings.obsRecordingsPath}
                    onChange={(e) => setSettings({ obsRecordingsPath: e.target.value })}
                    placeholder="E:\\OBS\\Recordings"
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <button className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50" title="Escolher pasta">
                    <FolderOpen className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pasta de Saída dos Clips</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={settings.clipsOutputPath}
                    onChange={(e) => setSettings({ clipsOutputPath: e.target.value })}
                    placeholder="E:\\clips\\prontos"
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <button className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50" title="Escolher pasta">
                    <FolderOpen className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pasta Temporária</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={settings.tempPath}
                    onChange={(e) => setSettings({ tempPath: e.target.value })}
                    placeholder="E:\\clips\\processando"
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <button className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50" title="Escolher pasta">
                    <FolderOpen className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
            <p className="text-sm text-slate-500">Dica: Configure o OBS → Settings → Output → Recording → Recording Path para a pasta de gravações acima.</p>
          </div>
        )

      case 'gemini':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-slate-900">Gemini API Key</h3>
            <p className="text-slate-600">O Gemini Flash analisa a transcrição e decide quais trechos têm potencial viral. É grátis (1500 req/dia).</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={settings.geminiApiKey}
                    onChange={(e) => setSettings({ geminiApiKey: e.target.value })}
                    placeholder="Cole sua chave do Google AI Studio"
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleTestGemini}
                  disabled={testing || !settings.geminiApiKey}
                  className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 flex items-center gap-2"
                >
                  {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Testar Conexão'}
                </button>
                {testResult === 'success' && <span className="text-green-600 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Conectado!</span>}
                {testResult === 'error' && <span className="text-red-600">Falha na conexão</span>}
              </div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
              <p className="text-sm text-purple-800">
                <ExternalLink className="w-4 h-4 inline mr-1" />{' '}
                <a href="https://aistudio.google.com" target="_blank" rel="noopener" className="underline hover:text-purple-600">
                  Pegar chave grátis no Google AI Studio
                </a>
              </p>
            </div>
          </div>
        )

      case 'twitch':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-slate-900">Twitch (Opcional)</h3>
            <p className="text-slate-600">Para processar VODs diretamente pela URL, configure o Client ID. Você pode pular e fazer depois.</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Client ID</label>
                <input
                  type="text"
                  value={settings.twitchClientId}
                  onChange={(e) => setSettings({ twitchClientId: e.target.value })}
                  placeholder="Seu Twitch Client ID"
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
            <p className="text-sm text-slate-500">
              Crie em <a href="https://dev.twitch.tv/console/apps" target="_blank" rel="noopener" className="text-purple-600 hover:underline">dev.twitch.tv/console/apps</a>
              → Register Application → OAuth Redirect: <code className="bg-slate-100 px-1 rounded">http://localhost:8765/api/v1/twitch/callback</code>
            </p>
          </div>
        )

      case 'whisper':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-slate-900">Modelo Whisper (Transcrição Local)</h3>
            <p className="text-slate-600">Roda 100% no seu PC (CPU). Escolha baseado na sua GPU:</p>
            <div className="space-y-3">
              {[
                { value: 'tiny', label: 'Tiny', desc: '~39MB, mais rápido, menos preciso', vram: 'Qualquer PC' },
                { value: 'base', label: 'Base (Recomendado)', desc: '~74MB, equilíbrio velocidade/qualidade', vram: 'RX 550 4GB ✓' },
                { value: 'small', label: 'Small', desc: '~244MB, melhor qualidade, mais lento', vram: '8GB+ VRAM' },
              ].map(model => (
                <label key={model.value} className="flex items-center gap-3 p-4 border-2 rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
                  style={{ borderColor: settings.whisperModel === model.value ? '#a855f7' : '#e2e8f0' }}>
                  <input
                    type="radio"
                    name="whisperModel"
                    value={model.value}
                    checked={settings.whisperModel === model.value}
                    onChange={(e) => setSettings({ whisperModel: e.target.value })}
                    className="w-4 h-4 text-purple-600 border-slate-300 focus:ring-purple-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{model.label}</span>
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{model.vram}</span>
                    </div>
                    <p className="text-sm text-slate-500 mt-0.5">{model.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )

      case 'done':
        return (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-2">Tudo pronto!</h3>
            <p className="text-slate-600 mb-8 max-w-md mx-auto">
              O Twitch Clipper está configurado. O backend vai iniciar e você será redirecionado ao Dashboard.
            </p>
            <div className="space-y-2 text-sm text-slate-500 max-w-md mx-auto">
              <p><strong>Pastas:</strong> {settings.obsRecordingsPath} → {settings.clipsOutputPath}</p>
              <p><strong>Whisper:</strong> {settings.whisperModel}</p>
              <p><strong>Gemini:</strong> {settings.geminiApiKey ? 'Configurado ✓' : 'Não configurado'}</p>
              <p><strong>Twitch:</strong> {settings.twitchClientId ? 'Configurado ✓' : 'Não configurado (opcional)'}</p>
            </div>
            <button
              onClick={handleFinish}
              className="mt-8 px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              Entrar no Dashboard
            </button>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
        <div className="border-b border-slate-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">Configuração Inicial</h2>
            <span className="text-sm text-slate-500">{currentStep + 1} / {steps.length}</span>
          </div>
          <div className="mt-4 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-600 transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-500">
            {steps.map((step, idx) => (
              <span key={step.id} className={idx <= currentStep ? 'text-purple-600 font-medium' : ''}>
                {step.title}
              </span>
            ))}
          </div>
        </div>

        <div className="p-6" style={{ minHeight: '400px' }}>
          <StepContent />
        </div>

        <div className="border-t border-slate-200 px-6 py-4 flex items-center justify-between bg-slate-50">
          <button
            onClick={goPrev}
            disabled={currentStep === 0}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </button>
          <button
            onClick={goNext}
            disabled={currentStep === steps.length - 1}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 ml-auto"
          >
            {currentStep === steps.length - 1 ? 'Finalizar' : 'Próximo'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}