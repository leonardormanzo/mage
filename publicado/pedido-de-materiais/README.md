# Pedir Material

Protótipo mobile navegável para trabalhadores solicitarem materiais numa
**reforma de apartamento** — fase → categoria/material → quantidade → dados
do pedido → revisão → confirmação, com histórico em "Meus pedidos". Feito
para aprovação visual e de fluxo antes de integrar ao aplicativo real.

Catálogo com 6 fases típicas de reforma de unidade (Demolição, Alvenaria,
Instalações, Revestimentos, Pintura, Acabamentos) — sem fundação, estrutura
ou cobertura, que são intervenções no prédio, não na unidade.

Obra fictícia fixa: **Residencial Horizonte** (OB-2026-014, São Paulo — SP).

## Como rodar

```sh
npm install
npm run dev              # http://localhost:5173
```

Outros comandos:

```sh
npm run build             # build de produção normal (dist/), assets com hash
npm run build:singlefile  # um único index.html autocontido (dist-singlefile/)
npm run preview           # serve o build normal localmente
npm run lint              # oxlint
```

O build `singlefile` embute CSS, JS e fontes em base64 num só arquivo HTML —
dá pra abrir direto no navegador (duplo clique) sem servidor, ou publicar como
demo compartilhável. Nenhum dos dois builds faz chamada de rede em tempo de
execução.

## Stack

React 18 + TypeScript + Vite, CSS Modules (sem framework de UI), ícones
[lucide-react](https://lucide.dev), fontes Inter + Plus Jakarta Sans
auto-hospedadas via `@fontsource` (sem CDN). Estado global em Context +
`useReducer`, navegação interna própria (pilha simples, sem `react-router` —
app pequeno o suficiente para não precisar). Tudo salvo em `localStorage`, sem
backend.

## Estrutura

```
src/
├── components/
│   ├── ui/            componentes genéricos (Button, Sheet, TextField, ...)
│   ├── layout/         casca do app (Shell, TopBar, ScreenHeader, BottomNav)
│   ├── onboarding/      captura de nome (primeiro acesso)
│   ├── home/            tela Início
│   ├── order/           fluxo "Pedir material" (fase → materiais → revisão)
│   ├── myorders/         "Meus pedidos" + detalhe
│   └── connectivity/     painel de demonstração do modo offline
├── state/              reducer, contexto, chaves de localStorage, telas
├── data/                catálogo (6 fases/categorias/materiais), status, obra
├── types/               modelos de domínio
└── utils/                formatação, validação, storage, id
```

## O que funciona de verdade

- Nome do solicitante, catálogo, pedidos e pedido em andamento persistem em
  `localStorage` — sobrevivem a reload.
- Validação de quantidade (inteiro vs. decimal por unidade), data mínima,
  campos obrigatórios.
- Merge automático ao adicionar um material já presente no pedido.

## O que é só simulação

- O indicador "Sem internet" / "Aguardando sincronização" é uma
  demonstração visual (painel "Ver simulação de modo offline") — não há
  detecção real de rede nem sincronização com servidor algum.
- Não há envio para nenhum sistema de escritório: a tela de sucesso deixa
  isso explícito ("simulada nesta versão").
- 5 pedidos fictícios (um por status) vêm pré-carregados na primeira visita
  para demonstrar a tela "Meus pedidos" com estados variados.

## Falta para terminar

- Integração real com o sistema do escritório (hoje só grava local).
- Autenticação / identificação real do trabalhador (hoje é só um nome livre).
- Sincronização offline de verdade (Service Worker, fila de envio) — hoje é
  só a simulação visual descrita acima.
- Cobertura de teste automatizada (o protótipo foi validado manualmente e via
  browser automation ponta a ponta; não tem suíte de testes).
