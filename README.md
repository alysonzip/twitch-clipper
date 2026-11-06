# Twitch Clipper

App desktop standalone para Windows que transforma suas lives da Twitch em clips
verticais virais — de forma automática e 100% local.

[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)
[![Plataforma](https://img.shields.io/badge/plataforma-Windows%2010%2F11-0078D6.svg)](#requisitos)
[![Electron](https://img.shields.io/badge/Electron-30-47848F.svg)](https://www.electronjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org/)
[![Versão](https://img.shields.io/badge/vers%C3%A3o-0.1.0-orange.svg)](CHANGELOG.md)

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração inicial](#configuração-inicial)
- [Configuração do OBS](#configuração-do-obs)
- [Como usar](#como-usar)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Desenvolvimento](#desenvolvimento)
- [Build e empacotamento](#build-e-empacotamento)
- [Documentação](#documentação)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Funcionalidades

- 🎬 **Pós-Live**: Processa VODs da Twitch e cria clips verticais 9:16
- 🔴 **Tempo Real**: Monitora a pasta do OBS e cria clips durante a live (latência de 2-5 min)
- 🤖 **IA Híbrida**: Whisper local (legendas) + Gemini Flash grátis (análise viral)
- 📱 **Formato Vertical**: 1080x1920 para Reels, TikTok e Shorts
- 👤 **Face Tracking**: Corte centralizado no rosto (YOLOv8n)
- 📝 **Legendas Karaoke**: Sincronizadas palavra por palavra
- 🎯 **Títulos Hook**: Texto de gancho nos primeiros 3 segundos
- 💾 **100% Local**: Seus dados e clips ficam na máquina (pasta configurável)
- 📦 **Standalone**: Instalador `.exe`, sem Docker aparente

## Requisitos

### Para usar o aplicativo

| Item | Requisito |
| --- | --- |
| Sistema | Windows 10/11 (64-bit) |
| Vídeo | GPU com suporte a DirectML (NVENC para encode H.264) — há fallback para CPU |
| Memória | 8 GB de RAM ou mais (recomendado) |
| Disco | ~2 GB para modelos de IA + espaço para os clips |
| FFmpeg | Deve estar no `PATH` ou em `C:\ffmpeg\bin` |

### Para desenvolver

| Item | Requisito |
| --- | --- |
| Node.js | 20 ou superior (com npm) |
| Python | 3.11 |
| [uv](https://docs.astral.sh/uv/) | Gerenciador de pacotes Python |
| FFmpeg | No `PATH` ou em `C:\ffmpeg\bin` |
| Redis | Opcional — necessário apenas para a fila de jobs em produção (veja `docker-compose.yml`) |
| Git | Para clonar e versionar |

## Instalação

1. Baixe o instalador gerado em `apps/frontend/dist_electron/` (`Twitch Clipper Setup <versão>.exe`)
2. Execute e siga o assistente de instalação
3. Na primeira abertura, complete o assistente de configuração (veja abaixo)

> Não quer instalar? A pasta `win-unpacked/` gerada junto ao instalador contém uma
> versão portátil: basta executar `Twitch Clipper.exe`.

## Configuração inicial

Na primeira execução o assistente pede:

- **Pastas** do OBS (gravações) e de saída dos clips
- **Gemini API Key** — grátis em [aistudio.google.com](https://aistudio.google.com)
- **Twitch Client ID** — opcional, necessário para baixar VODs
- **Modelo Whisper** — recomendado `base` para placas com pouca VRAM (ex.: RX 550 4 GB)

## Configuração do OBS

```
Settings → Output → Recording:
  - Recording Path: E:\OBS\Recordings (ou a pasta que você configurar no app)
  - Recording Format: MP4
  - Encoder: NVENC H.264
  - Keyframe Interval: 2s
```

## Como usar

### Pós-Live (VODs)

1. Abra a aba **Dashboard** ou **Jobs**
2. Clique em **Processar VOD**
3. Cole a URL do VOD da Twitch
4. Aguarde o processamento
5. Os clips ficam prontos na pasta de saída configurada

### Tempo Real (Live)

1. Configure o OBS para gravar na pasta monitorada
2. Abra a aba **Ao Vivo**
3. Clique em **Iniciar Monitoramento**
4. Faça sua live normalmente
5. Os clips virais aparecem automaticamente na pasta de saída

## Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Electron GUI  │────▶│  Python Backend  │────▶│   FFmpeg/GPU    │
│  (React/Vite)   │     │  (FastAPI/ARQ)   │     │   Renderer      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                         │
                              ▼                         ▼
                        ┌──────────────┐          ┌──────────────┐
                        │   SQLite     │          │   Whisper    │
                        │   (jobs,     │          │   (local)    │
                        │   clips,     │          └──────────────┘
                        │   settings)  │
                        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │   Redis      │
                        │   (queue)    │
                        └──────────────┘
```

O processo principal do Electron sobe o `backend.exe` (API FastAPI em
`http://localhost:8765`) e só abre a janela quando o backend responde.

## Tecnologias

- **Frontend**: Electron 30, React 18, Vite 5, TypeScript, TailwindCSS, Zustand, React Router
- **Backend**: Python 3.11, FastAPI, Uvicorn, ARQ, SQLModel, Redis, SQLite
- **IA**: faster-whisper (CTranslate2), Google Gemini Flash, YOLOv8n (ONNX/DirectML)
- **Vídeo**: FFmpeg (NVENC / libx264), ffmpeg-python
- **Empacotamento**: PyInstaller (backend) e Electron Builder / NSIS (instalador)

## Estrutura do projeto

```
twitch-clipper/
├── apps/
│   ├── backend/                  # API + workers (Python 3.11 / FastAPI)
│   │   ├── src/
│   │   │   ├── api/routes/       # endpoints REST (clips, jobs, live, settings, twitch)
│   │   │   ├── models/           # modelos SQLModel (clip, job, settings)
│   │   │   ├── schemas/          # schemas (gemini, render, whisper)
│   │   │   ├── services/         # twitch, file watcher, settings
│   │   │   ├── workers/          # orchestrator, gemini, render, whisper
│   │   │   └── main.py           # entrada da API
│   │   ├── resources/            # fontes e modelos auxiliares
│   │   ├── tests/                # testes (pytest)
│   │   ├── build_backend.py      # empacota o backend com PyInstaller
│   │   ├── twitch_clipper.spec   # spec do PyInstaller
│   │   └── pyproject.toml
│   └── frontend/                 # App desktop (Electron + React)
│       ├── electron/             # processo main (main, preload, ipc, backend)
│       ├── src/
│       │   ├── components/       # Layout, VideoPlayer...
│       │   ├── pages/            # Dashboard, Jobs, Clips, Live, Settings, SetupWizard
│       │   └── store/            # estado global (Zustand)
│       ├── build/                # ícone do app + script NSIS custom (installer.nsh)
│       ├── tests/e2e/            # testes e2e (Cypress)
│       ├── vite.config.ts
│       └── package.json
├── docs/
│   ├── USER_GUIDE.md             # guia do usuário final
│   └── DEVELOPER_GUIDE.md        # guia do desenvolvedor
├── docker-compose.yml            # Redis para desenvolvimento
├── package.json                  # workspace raiz (npm workspaces)
├── CHANGELOG.md
└── README.md
```

## Desenvolvimento

### 1. Instalar dependências

```bash
# Dependências Node (monorepo)
npm install

# Dependências Python (backend)
cd apps/backend
uv sync
cd ../..
```

### 2. Rodar em desenvolvimento

```bash
# Terminal 1 — backend (API em http://localhost:8765)
cd apps/backend
uv run python -m src.main

# Terminal 2 — interface (Vite em http://localhost:5173)
npm run dev --workspace=apps/frontend
```

Ou suba os dois de uma vez com `npm run dev` (usa `concurrently`).

### 3. Redis (opcional)

```bash
docker-compose up -d      # sobe um Redis local para a fila de jobs
```

### Scripts disponíveis

| Local | Comando | O que faz |
| --- | --- | --- |
| raiz | `npm run dev` | Sobe frontend + backend em paralelo |
| raiz | `npm run build` | Build de todos os workspaces |
| raiz | `npm run package` | Gera o instalador NSIS |
| `apps/frontend` | `npm run dev` | Vite dev server |
| `apps/frontend` | `npm run build` | Compila o renderer (`tsc && vite build`) e o processo Electron (`esbuild`) |
| `apps/frontend` | `npm run package` | Build + `electron-builder` (instalador em `dist_electron/`) |

## Build e empacotamento

Pipeline completa, na raiz do projeto:

```bash
# 1. Dependências
npm install
cd apps/backend && uv sync && cd ../..

# 2. (Opcional) Redis para testes
docker-compose up -d

# 3. Build completo + instalador NSIS
npm run package
```

O passo `npm run package` executa, em sequência:

1. **Renderer** — `tsc && vite build` → `apps/frontend/dist/`
2. **Electron** — `esbuild` empacota `electron/*.ts` → `apps/frontend/dist-electron/` (`main.mjs`, `preload.mjs`)
3. **Backend** — `apps/backend/build_backend.py` roda o PyInstaller e copia o `backend.exe` para `apps/frontend/backend/`
4. **Instalador** — `electron-builder` gera o NSIS em `apps/frontend/dist_electron/`
   (`Twitch Clipper Setup <versão>.exe` + a pasta portátil `win-unpacked/`)

> **Notas de build (Windows)**
> - O `electron-builder` está configurado com `npmRebuild: false` e
>   `signAndEditExecutable: false` no `package.json` do frontend. Isso evita,
>   respectivamente, a reinstalação destrutiva de dependências e o download do
>   `winCodeSign` (que falha ao extrair symlinks sem privilégio de administrador).
> - Para o ícone do `.exe` ser aplicado, mantenha `apps/frontend/build/icon.ico`.

Versão e release: `apps/frontend/release.js` faz bump de versão, build completo e cria a tag git.

## Documentação

- [Guia do Usuário](docs/USER_GUIDE.md) — instalação, uso e solução de problemas
- [Guia do Desenvolvedor](docs/DEVELOPER_GUIDE.md) — arquitetura, API e padrões de código
- [Changelog](CHANGELOG.md) — histórico de versões

## Contribuindo

Contribuições são bem-vindas! Resumo do fluxo:

1. Faça um fork do projeto
2. Crie uma branch: `git checkout -b feat/minha-feature`
3. Commit seguindo [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m "feat: adiciona nova funcionalidade"`
4. Abra um Pull Request descrevendo a mudança

Detalhes de arquitetura e padrões de código estão no [Guia do Desenvolvedor](docs/DEVELOPER_GUIDE.md).

## Licença

Distribuído sob a licença **MIT**. Veja [LICENSE](LICENSE) para mais detalhes.

---

> **Aviso**: use apenas com conteúdo próprio ou que você tenha direito de processar.
> Respeite os Termos de Serviço da Twitch e os direitos autorais dos criadores.
