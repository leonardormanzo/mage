# Síndico Inteligente

Aplicativo desktop local para gestão operacional de condomínios. O handoff original permanece em
`design_handoff_sindico_inteligente/`; a aplicação executável está em `sindico_app/`.

## Recursos

- Painel de ocorrências, tarefas, comunicados, contatos, espaços e reservas.
- Importação e indexação local de PDFs com SQLite FTS5, resposta com documento e página.
- Bloqueio de conflitos e horários inválidos em reservas.
- Prévia antes de alterações, backup SQLite e exportação JSON.
- Sem login, servidor remoto ou chave de IA obrigatória.

## Executar

Dê dois cliques em `launch_sindico.cmd`. Na primeira execução, o ambiente Python e as dependências
serão instalados. Os dados ficam em `%LOCALAPPDATA%\SindicoInteligente`.

Para desenvolvimento:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python run.py
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Execute `build_windows.cmd` para gerar `dist\Sindico Inteligente\Sindico Inteligente.exe`.

## Limites do MVP

A busca local apresenta o trecho mais relevante, sem inventar uma síntese. O adaptador opcional de
LLM fica reservado para uma próxima configuração. Comunicados são publicados apenas no registro
local; não há envio para moradores. O aplicativo é de usuário único.

