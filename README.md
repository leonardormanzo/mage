# Mage

Este repositório separa os arquivos públicos dos arquivos que devem permanecer
somente neste computador.

## Estrutura

- `publicado/`: conteúdo versionado e enviado ao GitHub.
- `privado/`: conteúdo exclusivamente local, ignorado pelo Git.
- `.gitignore`: regras que impedem o envio de arquivos privados e temporários.

## Regra prática

Coloque em `publicado/` apenas arquivos que podem ser vistos por qualquer pessoa.
Coloque em `privado/` rascunhos, credenciais, dados pessoais, exportações internas
e qualquer material que não deva aparecer no GitHub.

Antes de publicar, use `git status` para conferir exatamente o que será incluído.
