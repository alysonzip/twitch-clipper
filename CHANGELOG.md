# Changelog - Twitch Clipper

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- Implementação completa do aplicativo standalone para Windows
- Arquitetura híbrida: Whisper local (faster-whisper int8) + Gemini Flash (cloud)
- Electron + React + TypeScript + TailwindCSS frontend
- Python FastAPI + ARQ/Redis + SQLModel/SQLite backend
- Monitoramento de pasta OBS com debouncing para clips em tempo real
- Processamento de VODs pós-live via URL da Twitch
- Face-centered cropping com YOLOv8n ONNX (DirectML)
- Legendas estilo karaoke (ASS) com sincronização palavra por palavra
- Hook titles automáticos nos primeiros 3 segundos
- Formato vertical 9:16 (1080x1920) para Reels/TikTok/Shorts
- Criptografia DPAPI para credenciais Twitch no Windows
- PyInstaller para bundling do backend
- Electron Builder (NSIS) para instalador standalone
- Assistente de configuração (Setup Wizard) na primeira execução
- Interface completa: Dashboard, Clips, Jobs, Live, Settings
- Player de vídeo integrado com atalhos de teclado
- Testes unitários (pytest) e integração (backend + frontend Cypress)
- Documentação: USER_GUIDE.md, DEVELOPER_GUIDE.md, README.md

### Corrigido
- N/A (versão inicial)

### Removido
- N/A (versão inicial)

---

## [1.0.0] - 2026-11-06

### Adicionado
- **Core**: Aplicativo completo Twitch Clipper v1.0.0
- **Backend Workers**:
  - `WhisperWorker`: Transcrição local com faster-whisper (modelos tiny/base/small int8)
  - `GeminiWorker`: Análise viral com Google Gemini Flash (1500 req/dia grátis)
  - `FFmpegRenderer`: Renderização com NVENC, face tracking, legendas ASS, hook titles
  - `Orchestrator`: Coordenação de jobs VOD e live segments
  - `FileWatcher`: Monitoramento de pasta OBS com debounce (30s padrão)
- **API Routes**:
  - `/api/v1/clips`: CRUD de clips, busca, filtros, estatísticas
  - `/api/v1/jobs`: Gerenciamento de jobs, progresso, cancelamento, retry
  - `/api/v1/settings`: Configurações persistentes, validação, teste Gemini
  - `/api/v1/twitch`: OAuth, validação token, busca VOD, download
  - `/api/v1/live`: Controle de monitoramento ao vivo, status watcher
- **Models** (SQLModel/SQLite):
  - `Clip`: Metadados completos (score, reason, hook_title, paths, duração)
  - `Job`: Tipos vod/live_segment, status, progresso, result_clips, error_message
  - `Settings`: Singleton com criptografia DPAPI para secrets
- **Services**:
  - `SettingsService`: Singleton thread-safe, DPAPI encrypt/decrypt
  - `TwitchService`: OAuth PKCE, API Helix, download via yt-dlp
  - `FileWatcherService`: watchdog + debounce, integração ARQ
- **Frontend Pages**:
  - `Dashboard`: Stats cards, ações rápidas, jobs recentes
  - `Clips`: Grid responsivo, player modal, busca, filtros, delete
  - `Jobs`: Tabela com progresso, ações (cancelar, retry, ver clips)
  - `Live`: Monitoramento tempo real, logs, stats, controle OBS
  - `Settings`: Abas (Pastas, API, Twitch, Whisper, Render, Avançado)
  - `SetupWizard`: 4 passos guiados na primeira execução
- **Components**:
  - `Layout`: Sidebar navegação, header, responsivo
  - `VideoPlayer`: Controles customizados, atalhos, fullscreen
- **Store** (Zustand + persist):
  - Settings, clips, jobs, live state, UI state
  - Actions tipadas para todas as operações
- **Electron**:
  - `main.ts`: Janela, tray, menu, backend lifecycle, auto-updater ready
  - `preload.ts`: contextBridge seguro (api, events, store)
  - `backend.ts`: Process manager, health check, restart, logging
  - `ipc.ts`: Handlers para store, dialogs, shell, window controls
- **Build**:
  - `build_backend.py`: PyInstaller com hiddenimports, datas, binaries
  - `twitch_clipper.spec`: Configuração completa PyInstaller
  - `package.json` (frontend): electron-builder NSIS, extraResources
  - `release.js`: Script de versionamento, build, tag, release
- **Tests**:
  - Unit: models, settings, twitch, whisper, gemini, render, orchestrator, file_watcher
  - Integration: full VOD pipeline, live segment pipeline
  - E2E: Cypress GUI navigation, setup wizard, video player
- **Docs**:
  - `README.md`: Visão geral, instalação, uso, build
  - `USER_GUIDE.md`: Guia completo usuário final (PT-BR)
  - `DEVELOPER_GUIDE.md`: Arquitetura, desenvolvimento, contribuição
- **Config**:
  - `docker-compose.yml`: Redis para desenvolvimento
  - `.env.example`: Template variáveis ambiente
  - `pyproject.toml`: Dependências Python (uv)
  - `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`

### Corrigido
- N/A

### Removido
- N/A

---

## Formato de Versão

- **Major**: Mudanças breaking na API, arquitetura ou formato de dados
- **Minor**: Novas funcionalidades compatíveis
- **Patch**: Correções de bugs compatíveis

## Próximos Passos (v1.1.0 planejado)

- [ ] Suporte a múltiplas contas Twitch
- [ ] Agendamento de processamento (cron)
- [ ] Exportação direta para TikTok/Reels/Shorts API
- [ ] Templates de legenda personalizáveis
- [ ] Preview de clip antes de renderizar
- [ ] Notificações push (Windows toast)
- [ ] Backup/restauração de configurações
- [ ] Telemetria opcional (anônima)