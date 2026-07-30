# Mage — contexto para Claude Code

Repositório pessoal de Leonardo Manzo (Mago da IA). Separa projetos públicos
(`publicado/`) de conteúdo estritamente local (`privado/`, ignorado pelo Git).

## Como este repo funciona

- Cada projeto público vive em `publicado/<nome-do-projeto>/`, com seu próprio
  `README.md`, autocontido.
- Publicação é estática: `wrangler.toml` serve tudo a partir da raiz via
  Cloudflare, e `_redirects` manda `/` para `/publicado/portfolio/`.
- Antes de publicar, rode `git status` para conferir que nada de `privado/` foi
  incluído.
- Os padrões detalhados de cada tipo de projeto (site estático, app desktop
  Python, pipeline de IA) estão documentados em
  `.claude/skills/odin/knowledge.md`.

## Modo Odin

Para criar um novo app, site ou projeto neste repositório seguindo os padrões já
estabelecidos, use a skill `/odin` — ela ativa um modo autônomo que escolhe
sozinho as skills e ferramentas necessárias, consulta os padrões dos projetos
existentes e só pede confirmação para ações destrutivas ou que afetem sistemas
fora deste ambiente local (push, deploy, mudança de escopo combinado).
