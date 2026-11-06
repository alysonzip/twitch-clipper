# Guia do Desenvolvedor - Twitch Clipper

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Electron App (Frontend)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   React UI   │  │  Zustand     │  │   IPC / Preload      │  │
│  │  (Pages,     │  │  Store       │  │   (contextBridge)    │  │
│  │  Components) │  │              │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │             │
│         └─────────────────┼──────────────────────┘             │
│                           ▼                                    │
│                    ┌──────────────┐                            │
│                    │   Main Proc  │                            │
│                    │  (Window,    │                            │
│                    │   Tray,      │                            │
│                    │   Backend    │                            │
│                    │   Manager)   │                            │
│                    └──────┬───────┘                            │
└───────────────────────────┼────────────────────────────────────┘
                            │ HTTP/JSON (localhost:8765)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Python Backend (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   REST API   │  │   ARQ Queue  │  │   Workers            │  │
│  │  (Routes)    │  │  (Redis)     │  │  (Whisper, Gemini,   │  │
│  │              │  │              │  │   Render, Watcher)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │             │
│         └─────────────────┼──────────────────────┘             │
│                           ▼                                    │
│                    ┌──────────────┐                            │
│                    │   SQLite     │                            │
│                    │   (Jobs,     │                            │
│                    │   Clips,     │                            │
│                    │   Settings)  │                            │
│                    └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Estrutura do Projeto

```
twitch-clipper/
├── package.json                 # Root workspace config
├── docker-compose.yml           # Redis for dev
├── .env.example                 # Environment template
├── README.md
├── docs/                        # Documentation
├── apps/
│   ├── frontend/                # Electron + React app
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── electron/
│   │   │   ├── main.ts          # Electron main process
│   │   │   ├── preload.ts       # IPC context bridge
│   │   │   ├── backend.ts       # Backend process manager
│   │   │   └── ipc.ts           # IPC handlers
│   │   ├── src/
│   │   │   ├── main.tsx         # React entry
│   │   │   ├── App.tsx          # Routes + providers
│   │   │   ├── components/      # Reusable components
│   │   │   ├── pages/           # Page components
│   │   │   ├── store/           # Zustand store
│   │   │   ├── hooks/           # Custom hooks
│   │   │   └── types/           # TypeScript types
│   │   └── build/               # Electron builder assets
│   │
│   └── backend/                 # Python FastAPI backend
│       ├── pyproject.toml
│       ├── twitch_clipper.spec  # PyInstaller spec
│       ├── build_backend.py     # Build script
│       ├── src/
│       │   ├── main.py          # FastAPI app factory
│       │   ├── database.py      # SQLite + SQLModel
│       │   ├── models/          # SQLModel tables
│       │   ├── api/routes/      # REST endpoints
│       │   ├── services/        # Business logic
│       │   ├── workers/         # ARQ job workers
│       │   └── schemas/         # Pydantic schemas
│       ├── resources/
│       │   ├── models/          # Whisper, YOLOv8n ONNX
│       │   └── fonts/           # Montserrat Bold
│       └── tests/               # Pytest tests
```

## Desenvolvimento

### Pré-requisitos
- Node.js 20+
- Python 3.11+
- uv (Python package manager)
- Redis (via Docker)
- FFmpeg no PATH

### Instalação
```bash
# Instalar dependências
npm install
cd apps/backend && uv sync

# Subir Redis
docker-compose up -d

# Desenvolvimento (frontend + backend)
npm run dev
```

### Comandos Úteis
```bash
# Frontend
npm run dev          # Vite dev server
npm run build        # Build produção
npm run preview      # Preview build

# Backend
cd apps/backend
uv run uvicorn src.main:app --reload --port 8765
uv run pytest                    # Rodar testes
uv run pytest tests/test_models.py -v

# Build completo
npm run package                  # Gera instalador NSIS

# Apenas backend
cd apps/backend && python build_backend.py
```

## Adicionando Novos Workers

1. Crie o worker em `src/workers/novo_worker.py`
2. Defina schemas em `src/schemas/novo.py`
3. Adicione job ARQ no worker
4. Registre em `src/workers/orchestrator.py`:
   ```python
   class WorkerSettings:
       functions = [
           process_vod_job,
           process_live_segment_job,
           novo_job,  # Adicionar aqui
       ]
   ```
5. Crie testes em `tests/test_novo_worker.py`

## Adicionando Novas Rotas API

1. Crie arquivo em `src/api/routes/novo.py`
2. Defina router FastAPI
3. Importe e registre em `src/main.py`:
   ```python
   from src.api.routes import novo
   app.include_router(novo.router, prefix="/api/v1/novo", tags=["novo"])
   ```

## Banco de Dados (SQLModel)

### Criar Nova Tabela
```python
# src/models/novo.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Novo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    valor: int
    criado_em: datetime = Field(default_factory=datetime.utcnow)
```

### Registrar no `__init__.py`
```python
# src/models/__init__.py
from src.models.novo import Novo
__all__ = ["Clip", "Job", "Settings", "Novo"]
```

### Migration (SQLite)
- SQLite não suporta migrations nativas
- Para desenvolvimento: delete `data.db` e reinicie
- Para produção: use Alembic ou script manual

## Configurações (Settings)

### Adicionar Novo Campo
1. Adicione em `src/models/settings.py`
2. Adicione em `SettingsUpdate` schema em `src/api/routes/settings.py`
3. Adicione campo no formulário em `src/pages/Settings.tsx`
4. Atualize `defaultSettings` no store `src/store/useAppStore.ts`

## Empacotamento

### PyInstaller (Backend)
```bash
cd apps/backend
python build_backend.py
```
- Gera `dist/backend.exe`
- Copia para `apps/frontend/backend/` para Electron Builder

### Electron Builder (Frontend)
```bash
npm run package
```
- Gera `dist_electron/Twitch Clipper Setup x.x.x.exe`
- Configuração em `apps/frontend/package.json` → `build`

### Recursos Incluídos
- `backend.exe` + dependências Python
- Modelos Whisper (`resources/models/whisper-*-int8/`)
- YOLOv8n ONNX (`resources/models/yolov8n-face.onnx`)
- Fonte Montserrat (`resources/fonts/Montserrat-Bold.ttf`)
- FFmpeg (bundled ou sistema)

## Testes

### Backend (Pytest)
```bash
cd apps/backend
uv run pytest                           # Todos
uv run pytest tests/test_models.py -v   # Específico
uv run pytest tests/integration/ -v     # Integração (requer backend rodando)
```

### Frontend (Cypress)
```bash
cd apps/frontend
npx cypress open        # Interface gráfica
npx cypress run         # Headless
```

## Debugging

### Backend
- Logs: `stdout`/`stderr` do processo
- FastAPI docs: `http://localhost:8765/docs`
- Health: `http://localhost:8765/api/v1/health`

### Frontend
- DevTools: F12 na janela (dev mode)
- Console: `mainWindow.webContents.openDevTools()`
- React DevTools: Disponível no DevTools

### IPC
- Preload: `apps/frontend/electron/preload.ts`
- Main: `apps/frontend/electron/ipc.ts`
- Renderer: `window.api.*`, `window.events.*`

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `VITE_DEV_SERVER_URL` | URL do Vite dev server | `http://localhost:5173` |
| `BACKEND_PORT` | Porta do backend | `8765` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379` |

## Troubleshooting Comum

### Backend não conecta ao Redis
```bash
docker-compose up -d
docker-compose logs redis
```

### PyInstaller falha
- Verifique `hiddenimports` no `.spec`
- Verifique se `onnxruntime-directml` compila no Windows
- Tente `--noconfirm --clean`

### Electron não carrega backend
- Verifique `extraResources` no `package.json`
- Verifique caminho em `backend.ts`
- Logs do processo backend no console do Electron

### Modelo Whisper não carrega
- Verifique `resources/models/whisper-{model}-int8/`
- Baixe manualmente se necessário:
  ```bash
  faster-whisper-download base
  ```

## Contribuindo

1. Fork o repositório
2. Crie branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m "feat: adiciona nova funcionalidade"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

### Padrões de Commit
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes
- `chore:` Manutenção

## Licença

MIT - Veja LICENSE para detalhes.