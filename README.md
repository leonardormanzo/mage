# Mage

Este repositório separa os arquivos públicos dos arquivos que devem permanecer
somente neste computador.

## Estrutura

- `publicado/`: projetos versionados e enviados ao GitHub.
  - `diario-de-obra/`: projeto Diário de Obra.
  - `checklist-de-obra/`: projeto Checklist de Obra.
  - `vigia-obra-frontend/`: painel de inspeção (protótipo de interface) do Vigia Obra.
  - `vigia-obra-seguranca/`: pipeline Python que analisa vídeos de obra e sinaliza
    não-conformidades de segurança via Claude.
  - `sindico-inteligente/`: MVP desktop local-first para operação de condomínios e
    consulta documental com fontes.
  - `agenda-retratil/`: MVP desktop Windows com metas locais e integração segura com
    Google Calendar.
  - Há outros projetos nesta pasta; cada um tem o seu próprio `README.md`.
- `ch3-diario-obra/`: app de Diário de Obra (RDO) em produção, com git próprio e
  repositório privado no GitHub.
- `em-desenvolvimento/`: projetos locais ainda em andamento (e `estudos/`), ignorados
  pelo Git. Quando um projeto fica pronto, ele passa para `publicado/`.
- `privado/`: conteúdo exclusivamente local, ignorado pelo Git (documentos de
  clientes, rascunhos e arquivos pessoais).
- `projetos prontos/`: clones e demos de terceiros, ignorados pelo Git.
- `.gitignore`: regras que impedem o envio de arquivos privados e temporários.

## Regra prática

Crie uma subpasta dentro de `publicado/` para cada projeto que pode ser visto
por qualquer pessoa. Use `index.html` como arquivo inicial de projetos web.
Coloque em `privado/` rascunhos, credenciais, dados pessoais, exportações internas
e qualquer material que não deva aparecer no GitHub.

Antes de publicar, use `git status` para conferir exatamente o que será incluído.
