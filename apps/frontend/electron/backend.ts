import { spawn, ChildProcess } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = join(dirname(fileURLToPath(import.meta.url)), '..')

let backendProcess: ChildProcess | null = null

export async function setupBackend(): Promise<void> {
  // Backend setup (migrations, etc.)
  console.log('Backend setup complete')
}

export async function startBackend(): Promise<ChildProcess> {
  const isDev = process.env.VITE_DEV_SERVER_URL !== undefined

  if (isDev) {
    // Development: run with uv/uvicorn
    backendProcess = spawn('uv', ['run', 'uvicorn', 'src.main:app', '--port', '8765'], {
      cwd: join(__dirname, '../../backend'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONPATH: join(__dirname, '../../backend') },
    })
  } else {
    // Production: run bundled executable
    const backendPath = join(process.resourcesPath, 'backend', 'backend.exe')
    backendProcess = spawn(backendPath, {
      stdio: ['ignore', 'pipe', 'pipe'],
    })
  }

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend Error] ${data.toString().trim()}`)
  })

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
    backendProcess = null
  })

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err)
  })

  return backendProcess
}

export function stopBackend(): void {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

export function getBackendProcess(): ChildProcess | null {
  return backendProcess
}

export async function waitForBackend(maxRetries = 30): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('http://localhost:8765/api/v1/health')
      if (response.ok) {
        console.log('Backend is ready')
        return
      }
    } catch {
      // Not ready yet
    }
    await new Promise(r => setTimeout(r, 1000))
  }
  throw new Error('Backend failed to start within timeout')
}