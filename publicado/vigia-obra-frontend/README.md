# Vigia Obra — Painel de Inspeção (frontend)

Interface para o [`vigia-obra-seguranca`](../vigia-obra-seguranca) (pipeline
que analisa vídeos de obra e sinaliza não-conformidades de segurança do
trabalho via Claude). Exibe as ocorrências detectadas em cartões ou tabela,
com timestamp, severidade e confiança, além dos parâmetros de análise
(intervalo entre frames, modelo, nível de esforço).

**Conectado ao backend real** via um servidor local em `server/` (Node +
Express): você seleciona um vídeo, o servidor roda o `vigia_obra.main`
(Python) como subprocesso e repassa o NDJSON que ele emite, linha a linha,
para a página — sem simulação.

## Como rodar

1. Instale as dependências do backend Python (uma vez), em
   `../vigia-obra-seguranca`:

   ```sh
   cd ../vigia-obra-seguranca
   python -m venv .venv
   .venv\Scripts\activate       # Windows
   pip install -r requirements.txt
   ```

2. Instale as dependências do servidor local e inicie-o, com sua
   `ANTHROPIC_API_KEY` definida no ambiente:

   ```sh
   cd server
   npm install
   set ANTHROPIC_API_KEY=sk-ant-...   # Windows (cmd); no PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
   npm start
   ```

3. Abra `http://localhost:5731` — o servidor serve o `index.html` e expõe
   `POST /api/analyze` (upload do vídeo) e `GET /api/health` (diagnóstico:
   se o backend foi encontrado e se a API key está configurada).

Se preferir não usar o servidor Node, ainda é possível abrir `index.html`
diretamente no navegador para ver o layout — mas o botão "Iniciar análise"
vai falhar ao tentar chamar `/api/analyze` sem o servidor rodando.

## Como funciona a integração

- O upload do vídeo vai para `POST /api/analyze` (multipart/form-data, campo
  `video`, mais `interval`/`model`/`effort`).
- O servidor (`server/index.js`) salva o vídeo em um arquivo temporário, roda
  `python -m vigia_obra.main <video> --interval ... --model ... --effort ...`
  com `cwd` em `vigia-obra-seguranca/`, e repassa cada linha NDJSON do
  `stdout` do processo diretamente na resposta HTTP (streaming, sem buffer).
- O frontend lê a resposta como stream (`response.body.getReader()`), separa
  por linha e processa cada evento (`start` / `progress` / `error` / `done`)
  do mesmo jeito que antes processava os eventos simulados.
- Se o processo Python falhar antes de emitir `done` (dependência faltando,
  API key inválida, vídeo corrompido etc.), o servidor sintetiza um evento
  `error` com o final do `stderr` para aparecer na tela.

## Limitações conhecidas

- Sem fila/concorrência: uma análise por vez, pensado para uso local do
  gestor/SESMT, não para múltiplos usuários simultâneos.
- Sem persistência no navegador — resultados vivem só na página aberta,
  embora o `vigia_obra.main` também grave o JSON final em disco
  (`--output`, arquivo temporário do servidor).
