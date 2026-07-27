# Agenda Retrátil

Painel desktop local-first para Windows, com metas locais, interpretação determinística de
compromissos e integração segura com o Google Calendar.

## Demonstração pública

Abra `index.html` para experimentar a simulação interativa do painel retrátil. Metas, eventos,
chat e conexão com Google Agenda são simulados em memória nessa página e não acessam uma conta
real. O aplicativo desktop em `agenda_app/` contém a integração OAuth e exige confirmação antes
de alterar o calendário.

## Recursos

- Próximos sete dias do calendário principal do Google.
- Criação, edição e exclusão somente após prévia e confirmação.
- Proteção contra repetição por `request_id` e contra sobrescrita por `etag`.
- OAuth para aplicativo desktop; token armazenado no Gerenciador de Credenciais do Windows.
- Metas e sugestões persistidas em SQLite, com backup e exportação.
- Nenhuma chave de IA no HTML ou obrigatória para funcionar.

## Executar

Dê dois cliques em `launch_agenda.cmd`. Os dados locais ficam em
`%LOCALAPPDATA%\AgendaRetratil`.

Para conectar o Google, ative a Google Calendar API no Google Cloud, crie uma credencial OAuth do
tipo **Aplicativo para computador**, baixe o JSON e selecione-o no botão circular do cabeçalho.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python run.py
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Execute `build_windows.cmd` para gerar o executável em `dist`.

## Privacidade e limites

Eventos só são enviados ao Google após confirmação. Metas e sugestões permanecem locais. Não há
sincronização bidirecional de uma segunda base de eventos, portal de equipe ou IA paga no MVP.

