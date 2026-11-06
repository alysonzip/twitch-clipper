# Guia do Usuário - Twitch Clipper

## Visão Geral

O Twitch Clipper é um aplicativo standalone para Windows que cria clips virais automáticos das suas lives da Twitch. Ele funciona de duas formas:

1. **Pós-Live (VODs)**: Processa VODs completos e extrai os melhores momentos
2. **Tempo Real (Live)**: Monitora a pasta de gravação do OBS e cria clips durante a live

## Instalação

1. Baixe o instalador `Twitch Clipper Setup.exe`
2. Execute o instalador e siga as instruções
3. Na primeira execução, o assistente de configuração será aberto automaticamente

## Configuração Inicial (Assistente)

### 1. Pastas
- **Pasta de Gravações do OBS**: Onde o OBS salva os arquivos de gravação (ex: `E:\OBS\Recordings`)
- **Pasta de Saída dos Clips**: Onde os clips prontos serão salvos (ex: `E:\clips\prontos`)
- **Pasta Temporária**: Para arquivos intermediários (ex: `E:\clips\processando`)

### 2. Gemini API Key (Obrigatório)
- Acesse [Google AI Studio](https://aistudio.google.com)
- Crie uma API Key gratuita (1500 requisições/dia)
- Cole a chave no campo indicado
- Clique em "Testar Conexão" para verificar

### 3. Twitch (Opcional)
- Para processar VODs diretamente pela URL
- Crie em [Twitch Dev Console](https://dev.twitch.tv/console/apps)
- OAuth Redirect: `http://localhost:8765/api/v1/twitch/callback`

### 4. Modelo Whisper
- **Tiny**: Mais rápido, menos preciso (qualquer PC)
- **Base (Recomendado)**: Equilíbrio velocidade/qualidade (RX 550 4GB ✓)
- **Small**: Melhor qualidade, mais lento (8GB+ VRAM)

## Configuração do OBS

Para o monitoramento em tempo real funcionar corretamente:

```
Settings → Output → Recording:
  - Recording Path: E:\OBS\Recordings (sua pasta configurada)
  - Recording Format: MP4 (NÃO MKV/FLV)
  - Encoder: NVENC H.264 (usa GPU, mais rápido)
  - Keyframe Interval: 2s (para cortes precisos)
  - Rate Control: CBR
  - Bitrate: 6000 Kbps (recomendado para 1080p60)
```

## Como Usar

### Processar VOD (Pós-Live)
1. Abra a aba **Dashboard** ou **Jobs**
2. Clique em "Processar VOD"
3. Cole a URL do VOD da Twitch (ex: `https://twitch.tv/videos/123456789`)
4. Aguarde o processamento (alguns minutos dependendo da duração)
5. Clips prontos aparecerão na aba **Clips** e na pasta `E:\clips\prontos\`

### Monitoramento Ao Vivo (Tempo Real)
1. Configure o OBS conforme acima
2. Inicie a gravação no OBS
3. Abra a aba **Ao Vivo**
4. Clique em "Iniciar Monitoramento"
5. Faça sua live normalmente
6. Clips virais aparecerão automaticamente na pasta de saída (latência: 2-5 min)

### Visualizar e Gerenciar Clips
- Aba **Clips**: Grade com todos os clips, player integrado, filtros
- Clique no ícone ▶️ para reproduzir
- Clique em 📁 para abrir a pasta do clip
- Clique em 🗑️ para excluir

### Acompanhar Jobs
- Aba **Jobs**: Lista de todos os processamentos
- Status: Na fila → Processando → Concluído/Falhou
- Barra de progresso mostra etapa atual
- Botões: Cancelar, Tentar novamente, Ver clips

## Formato dos Clips

- **Resolução**: 1080x1920 (9:16 vertical)
- **Codec**: H.264 (NVENC) ou libx264 (CPU fallback)
- **FPS**: 30
- **Legendas**: Karaoke (palavra por palavra), Pop, ou Minimal
- **Face Tracking**: Corte centralizado no rosto detectado
- **Hook Title**: Título de gancho nos primeiros 3 segundos

## Solução de Problemas

### Backend não inicia
- Verifique se o Redis está rodando: `docker-compose up -d`
- Verifique porta 8765 livre
- Verifique antivírus não bloqueando `backend.exe`

### Clips não aparecem
- Verifique se a pasta do OBS está correta
- Verifique se o OBS está gravando em MP4
- Verifique logs na aba Jobs

### Gemini API erro
- Verifique se a chave está correta
- Verifique cota diária (1500 req/dia grátis)
- Teste na aba Configurações

### Face tracking não funciona
- Verifique se `yolov8n-face.onnx` está na pasta resources/models
- GPU deve suportar DirectML (RX 550 suporta)

### Whisper lento
- Use modelo "tiny" ou "base"
- Feche outros programas pesados
- Verifique se não está usando swap excessivo

## Atalhos do Player

| Tecla | Ação |
|-------|------|
| Espaço | Play/Pause |
| ← / → | Voltar/Avançar 5s |
| F | Tela cheia |
| M | Mutar/Desmutar |

## Pastas Importantes

| Pasta | Padrão | Função |
|-------|--------|--------|
| Gravações OBS | `E:\OBS\Recordings` | Monitorada para live |
| Clips Prontos | `E:\clips\prontos` | Saída final |
| Temporários | `E:\clips\processando` | Arquivos intermediários |
| Configurações | `%APPDATA%\TwitchClipper\data.db` | SQLite local |

## Suporte

- Logs: Aba Jobs → clique no job → ver logs
- Issues: GitHub do projeto
- Atualizações: Verificadas automaticamente na inicialização