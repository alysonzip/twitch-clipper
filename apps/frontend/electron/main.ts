import { app, BrowserWindow, Tray, Menu, nativeImage, shell, ipcMain, protocol } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawn, exec, ChildProcess } from 'child_process'
import { setupBackend } from './backend'
import { registerIpcHandlers } from './ipc'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Em desenvolvimento (app nao empacotado) carrega o servidor do Vite.
// Em producao carrega o HTML gerado em ./dist.
const DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL ?? (app.isPackaged ? null : 'http://localhost:5173')

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let backendProcess: ChildProcess | null = null
let isQuitting = false

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, 'preload.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    icon: join(__dirname, '../build/icon.ico'),
  })

  // Garante que a janela apareca mesmo se o renderer falhar ao carregar
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    console.error(`Falha ao carregar a interface (${errorCode}): ${errorDescription} - ${validatedURL}`)
    mainWindow?.show()
  })

  // Load URL
  try {
    if (DEV_SERVER_URL) {
      await mainWindow.loadURL(DEV_SERVER_URL)
      mainWindow.webContents.openDevTools()
    } else {
      await mainWindow.loadFile(join(__dirname, '../dist/index.html'))
    }
  } catch (err) {
    console.error('Erro ao carregar a interface:', err)
    mainWindow?.show()
  }

  mainWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault()
      mainWindow?.hide()
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

function createTray() {
  const iconPath = join(__dirname, '../build/icon.ico')
  const icon = nativeImage.createFromPath(iconPath)

  tray = new Tray(icon.resize({ width: 16, height: 16 }))

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Abrir Twitch Clipper',
      click: () => {
        mainWindow?.show()
        mainWindow?.focus()
      },
    },
    { type: 'separator' },
    {
      label: 'Pausar Monitoramento',
      click: () => {
        mainWindow?.webContents.send('live:pause')
      },
    },
    {
      label: 'Retomar Monitoramento',
      click: () => {
        mainWindow?.webContents.send('live:resume')
      },
    },
    { type: 'separator' },
    {
      label: 'Abrir Pasta de Clips',
      click: () => {
        mainWindow?.webContents.send('app:open-clips-folder')
      },
    },
    { type: 'separator' },
    {
      label: 'Sair',
      click: () => {
        isQuitting = true
        app.quit()
      },
    },
  ])

  tray.setToolTip('Twitch Clipper')
  tray.setContextMenu(contextMenu)

  tray.on('double-click', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })
}

async function startBackend() {
  const backendPath = DEV_SERVER_URL
    ? join(__dirname, '../../backend/src/main.py')
    : join(process.resourcesPath, 'backend', 'backend.exe')

  if (DEV_SERVER_URL) {
    // Dev mode: run with uvicorn
    backendProcess = spawn('uv', ['run', 'uvicorn', 'src.main:app', '--port', '8765'], {
      cwd: join(__dirname, '../../backend'),
      stdio: 'pipe',
    })
  } else {
    // Production: run bundled executable
    backendProcess = spawn(backendPath, {
      stdio: 'pipe',
    })
  }

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data}`)
  })

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend Error] ${data}`)
  })

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
    backendProcess = null
  })

  // Verifica o backend em segundo plano, sem bloquear a interface
  waitForBackend()
    .then(() => console.log('Backend is ready'))
    .catch((err) => console.error('Backend indisponivel:', err.message))
}

async function waitForBackend(maxRetries = 30): Promise<void> {
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

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

async function setupApp() {
  // Register custom protocol for OAuth callback
  protocol.handle('twitchclipper', (request) => {
    const url = new URL(request.url)
    if (url.pathname === '/callback') {
      mainWindow?.webContents.send('oauth:callback', url.searchParams.get('code'))
    }
    return new Response(null, { status: 200, headers: { Location: 'twitchclipper://callback' } })
  })

  // Cria a janela primeiro: a interface aparece independente do backend
  await createWindow()
  registerIpcHandlers(mainWindow!)

  try {
    createTray()
  } catch (err) {
    console.error('Falha ao criar o icone da bandeja:', err)
  }

  // Inicia o backend em segundo plano (best-effort)
  await setupBackend()
  startBackend().catch((err) => console.error('Falha ao iniciar backend:', err))

  // Auto-start if enabled
  const settings = await getSettings()
  if (settings.autoStart) {
    setupAutoStart(true)
  }
}

async function getSettings() {
  // In real implementation, fetch from backend
  return { autoStart: false }
}

function setupAutoStart(enable: boolean) {
  if (process.platform === 'win32') {
    const appPath = process.execPath
    const regCmd = enable
      ? `reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "TwitchClipper" /t REG_SZ /d "${appPath}" /f`
      : `reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "TwitchClipper" /f`

    exec(regCmd, (error) => {
      if (error) console.error('Auto-start setup failed:', error)
    })
  }
}

// App event handlers
app.whenReady().then(setupApp)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('before-quit', () => {
  isQuitting = true
  stopBackend()
})

app.on('will-quit', () => {
  stopBackend()
})

// Handle single instance
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}