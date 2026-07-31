# Painel Obra Desktop

Cópia exata do app **Agenda Overlay** (`projetos prontos/desktop_calendar`) — painel de agenda retrátil para Windows, encostado na borda direita da tela, com animação e cantos arredondados via Win32 (`overrideredirect` + `SetWindowRgn`), não pywebview/HTML. Sincroniza com o Google Agenda e aceita compromissos em linguagem natural.

Sobre essa base foi adicionada apenas uma função: **publicar um painel público estático** (itens em aberto, metas da semana, metas gerais e o retrato da última sincronização com o Google Agenda) para colar o link na descrição de um grupo do WhatsApp.

## O que é exatamente igual ao original

- `calendar_app/adapter.py`, `google_adapter.py`, `oauth.py`, `credentials.py`, `models.py`, `service.py`, `suggestions.py`, `ai_parser.py`, `ui.py`, `overlay_ui.py` (com pequenos acréscimos, ver abaixo)
- `run.py`, `launch_agenda.cmd`, `requirements.txt`, `.env.example`, `.gitignore`, `simulacao.html`, `tests/`

## O que foi adicionado

- **`calendar_app/board.py`** — persistência local (SQLite) de itens em aberto, metas da semana/gerais e retrato da última sincronização de eventos.
- **`calendar_app/publish.py`** — gera a página pública estática a partir do `board.py`.
- **No painel (`overlay_ui.py`)**: os cards "Goal Week"/"Goal Diário" (que eram texto fixo no original) agora são **Metas da semana** e **Metas gerais**, editáveis (`+` no cabeçalho do card, `×` para remover). Um novo card **Itens em aberto** foi adicionado logo abaixo. Um botão **Publicar painel** foi adicionado no rodapé, abaixo do botão de conectar/atualizar o Google Agenda.
- Cada `refresh()` bem-sucedido agora também grava um retrato dos eventos no `board.py`, para que o painel público possa ser publicado mesmo com o Google desconectado no momento.

## Publicar o painel público

1. Preencha itens em aberto e metas pelo painel (ícone `+` em cada card).
2. Conecte o Google Agenda normalmente para os próximos 7 dias aparecerem.
3. Clique em **Publicar painel** no rodapé — isso escreve `publicado/painel-obra/index.html` (pasta irmã, mesmo destino usado pelo restante do site estático deste repositório).
4. Faça commit/deploy do site e cole o link de `painel-obra` na descrição do grupo do WhatsApp da obra.

A página pública é somente leitura e reflete a última publicação manual — não é ao vivo.

## Instalação e uso

Mesmos passos do projeto original — veja `DOCUMENTACAO.md` em `projetos prontos/desktop_calendar` para o detalhamento completo (OAuth do Google, chave da Anthropic, testes). Resumo:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Ou dê dois cliques em `launch_agenda.cmd` para rodar sem console.
