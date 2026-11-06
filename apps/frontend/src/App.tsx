import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Clips from './pages/Clips'
import Jobs from './pages/Jobs'
import Live from './pages/Live'
import Settings from './pages/Settings'
import SetupWizard from './pages/SetupWizard'
import { useAppStore } from './store/useAppStore'

function App() {
  const { isFirstRun, settingsLoaded } = useAppStore()

  if (!settingsLoaded) {
    return <div className="min-h-screen flex items-center justify-center">Carregando...</div>
  }

  if (isFirstRun) {
    return <SetupWizard />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/clips" element={<Clips />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/live" element={<Live />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App