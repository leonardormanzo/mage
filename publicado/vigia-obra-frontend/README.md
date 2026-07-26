# Vigia Obra — Painel de Inspeção (frontend)

Protótipo de interface para o [`vigia-obra-seguranca`](../vigia-obra-seguranca)
(pipeline que analisa vídeos de obra e sinaliza não-conformidades de segurança do
trabalho via Claude). Exibe as ocorrências detectadas em cartões ou tabela, com
timestamp, severidade e confiança, além dos parâmetros de análise (intervalo entre
frames, modelo, nível de esforço).

**Ainda não está conectado ao backend real.** O botão "Iniciar análise" roda uma
simulação com dados mocados (`mockEvents`, dentro do próprio `index.html`),
seguindo o mesmo contrato NDJSON que o `main.py` do backend emite (ver seção
"Protocolo para integração com um frontend local" no README do
`vigia-obra-seguranca`).

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Falta para terminar

Conectar de fato ao `vigia-obra-seguranca`: rodar o processo Python via
child_process/subprocess (Electron, Tauri ou um backend Node) e substituir a
`runSimulation()`/`mockEvents` pela leitura real do NDJSON linha a linha.
