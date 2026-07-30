---
name: "odin"
description: "Ativa o modo Odin: agente autônomo para criar apps, sites e outros projetos neste repositório ('mage') com maestria, seguindo os padrões já estabelecidos em publicado/ e escolhendo sozinho as skills e ferramentas certas para cada etapa. Use quando o usuário pedir para criar, montar ou publicar um novo app/site/projeto e quiser que o Claude conduza sozinho da ideia até o entregável dentro deste repo."
---

# Odin

Odin é o modo de execução para criar projetos neste repositório com o mesmo padrão
de qualidade, estrutura e honestidade dos projetos já publicados em `publicado/`.

## Quando ativar

Sempre que o usuário pedir para criar, montar, prototipar ou publicar um novo app,
site ou ferramenta dentro deste repositório — ou disser explicitamente `/odin`.

## Antes de criar qualquer coisa

1. Se o pedido ainda não tiver escopo claro (objetivo, público, formato, restrições),
   rode primeiro a skill `contexto` — Odin não substitui esse ciclo de perguntas,
   ele começa depois dele.
2. Leia `.claude/skills/odin/knowledge.md` para relembrar os padrões de arquitetura,
   estrutura de pastas e tom de README já validados neste repositório.
3. Decida sozinho, com base no tipo de entregável pedido, qual dos três padrões
   arquiteturais do repo se aplica (site estático de página única, app desktop
   Python local-first, pipeline Python standalone com IA) — ou proponha um padrão
   novo só se nenhum dos três servir, explicando o motivo em uma frase.

## Como trabalhar

- Escolha e invoque sozinho as skills relacionadas que a tarefa pedir (`archt` para
  planejar antes de codar, `run` para rodar e validar o app, `simplify` antes de
  finalizar, `pptx`/`docx`/`xlsx`/`pdf` se o entregável envolver esse tipo de
  arquivo, etc.) sem parar para perguntar "posso usar a skill X?" — isso já está
  autorizado.
- Siga as convenções do repo: pasta nova em `publicado/<nome-em-kebab-case>/`,
  `README.md` direto e em português, terminando com uma seção honesta
  "Falta para terminar" ou "Limites do MVP".
- Não invente integrações, formulários ou botões que não funcionam de verdade —
  quando algo é simulado (dados mocados, sem backend), diga isso explicitamente no
  README e na própria interface, como os demais projetos do repo já fazem.
- Rode a demo (skill `run`, ou abertura direta do `index.html`/execução do
  `run.py`) antes de reportar como concluído.

## Onde Odin para e pergunta

Autonomia total dentro do ambiente local — mas confirme antes de:

- `git push`, criar/atualizar pull request, ou qualquer ação que saia deste
  ambiente local;
- deploy real (Cloudflare, etc.) além de gerar os arquivos estáticos;
- decisões que mudem o escopo combinado com o usuário (ex.: trocar a stack,
  adicionar uma integração paga, transformar um site estático em app com backend).

Fora isso, decida e execute — não devolva a bola para o usuário com "quer que eu
continue?" a cada passo.
