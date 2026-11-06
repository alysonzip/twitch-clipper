import { ipcMain, shell, BrowserWindow } from 'electron'

export function registerIpcHandlers(mainWindow: BrowserWindow) {
  // App handlers
  ipcMain.handle('app:open-folder', async (_, path: string) => {
    await shell.openPath(path)
  })

  ipcMain.handle('app:open-external', async (_, url: string) => {
    await shell.openExternal(url)
  })

  // Live status forwarding (from backend to renderer)
  ipcMain.on('live:pause', () => {
    // Forward to backend via API
    fetch('http://localhost:8765/api/v1/live/pause', { method: 'POST' }).catch(console.error)
  })

  ipcMain.on('live:resume', () => {
    fetch('http://localhost:8765/api/v1/live/resume', { method: 'POST' }).catch(console.error)
  })

  // Window management
  ipcMain.on('window:minimize', () => {
    mainWindow?.minimize()
  })

  ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })

  ipcMain.on('window:close', () => {
    mainWindow?.hide()
  })

  // Settings sync
  ipcMain.on('settings:updated', () => {
    // Notify renderer that settings changed
    mainWindow?.webContents.send('settings:changed')
  })
}