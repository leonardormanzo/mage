# Padrões dos projetos em publicado/ (base de conhecimento do Odin)

## Estrutura geral

- Cada projeto é uma subpasta `publicado/<nome-kebab-case>/` com seu próprio `README.md`.
- `index.html` é o arquivo de entrada de qualquer demo web.
- Publicação estática do repo inteiro via Cloudflare (`wrangler.toml`, assets servidos
  a partir da raiz) + `_redirects` mandando `/` para `/publicado/portfolio/`.
- `privado/`, `cv leo/`, `projetos prontos/` nunca vão para o Git (ver `.gitignore`) —
  nada sensível ou pessoal deve vazar para `publicado/`.

## Três arquiteturas recorrentes

### 1. Site estático de página única (sem backend)

Exemplos: `checklist-de-obra`, `diario-de-obra`, `mago-da-ia`, `portfolio`,
`vigia-obra-frontend`.

- Um único `index.html` autocontido (HTML+CSS+JS inline, sem build step, sem framework).
- Estado vive em memória do navegador (ou `localStorage` para preferências como tema,
  ver `portfolio`) — não persiste dados reais entre reloads a menos que seja o
  objetivo explícito.
- README explica em uma frase o que o app faz, deixa claro "página única, sem
  backend", como abrir (`abra index.html` ou `npx serve .`), e fecha com "Falta para
  terminar" listando honestamente o que é só protótipo/mock.
- Dados/ações simuladas (ex: importação de PDF, envio de formulário) ficam claramente
  marcadas como simulação — nunca um botão que finge funcionar sem avisar.

### 2. App desktop Python local-first

Exemplos: `sindico-inteligente`, `agenda-retratil`.

- Estrutura: `<nome>_app/` com o código, `run.py` como entrypoint, `requirements.txt`,
  `tests/` com `unittest`.
- `launch_<nome>.cmd` para clique duplo (usuário Windows não-técnico),
  `build_windows.cmd` gera executável via PyInstaller em `dist/`.
- Dados ficam localmente em `%LOCALAPPDATA%\<Nome>` (SQLite), com backup/exportação.
- Sem login, sem servidor remoto, sem chave de IA obrigatória para o MVP funcionar.
- Integrações externas (Google Calendar, LLM) sempre atrás de confirmação explícita do
  usuário antes de qualquer escrita; nunca bidirecional/automático sem prévia.
- README traz seção "Executar" com os comandos exatos (venv, pip install, run.py,
  testes) e "Limites do MVP" honesto.

### 3. Pipeline Python standalone com IA

Exemplo: `vigia-obra-seguranca`.

- CLI (`python -m pacote.main arquivo --flags`), `.env.example` para a chave de API
  (nunca commitar a real).
- Protocolo de saída documentado: NDJSON no stdout linha a linha (para um frontend
  consumir em tempo real via subprocess) + arquivo JSON final gravado em disco.
- Parâmetros de custo/modelo expostos (`--model`, `--effort`) e documentados no
  README, incluindo qual modelo usar por padrão e qual usar para reduzir custo em
  volumes grandes.
- Disclaimer explícito de que é uma ferramenta assistiva, não substitui revisão
  humana — e isso aparece tanto no README quanto na saída real do programa (não só em
  texto solto).

## Tom e convenções de README

- Português, direto, primeira linha resume o que o projeto faz.
- Sempre uma seção final honesta sobre o que falta / limites do MVP — nunca esconder
  que algo é mockado.
- Nomes de pasta em kebab-case; nomes de exibição em título (ex.: "Síndico
  Inteligente").

## Modelos de IA usados no repo

- `vigia-obra-seguranca` usa Claude via API: modelo mais capaz como padrão de
  qualidade, um modelo mais rápido/barato como opção para reduzir custo em volume
  alto. Ao adicionar IA a um novo projeto, seguir esse padrão: expor o modelo e o
  nível de esforço como parâmetro, nunca hardcoded, e nomear os modelos atuais
  explicitamente (conferir os IDs vigentes em vez de reutilizar nomes antigos).
