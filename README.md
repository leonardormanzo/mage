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
- `privado/`: conteúdo exclusivamente local, ignorado pelo Git.
- `.gitignore`: regras que impedem o envio de arquivos privados e temporários.

## Regra prática

Crie uma subpasta dentro de `publicado/` para cada projeto que pode ser visto
por qualquer pessoa. Use `index.html` como arquivo inicial de projetos web.
Coloque em `privado/` rascunhos, credenciais, dados pessoais, exportações internas
e qualquer material que não deva aparecer no GitHub.

Antes de publicar, use `git status` para conferir exatamente o que será incluído.
