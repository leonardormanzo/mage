# Habit Tracker

Web app de rastreamento de hábitos: marque hábitos diários, veja a grade da semana,
acompanhe streaks e completude em gráficos, e organize tarefas soltas da semana.
Tudo roda no navegador — nenhum dado sai da sua máquina.

Inspirado no estilo visual de tracker "matriz de hábitos" popular em contas como
`@limitlessxmindsets` no Instagram: linhas de hábitos, colunas de dias, streaks em
destaque.

## Stack

- React 18 + TypeScript + Vite
- Zustand para estado global
- IndexedDB (via `idb`) para persistência local — sem backend, sem conta, sem sync
  entre dispositivos
- Tailwind CSS v4 para estilo (tema dark)
- Recharts para o gráfico de completude semanal

## Executar

```bash
npm install
npm run dev      # servidor de desenvolvimento
npm run build    # build de produção em dist/
npm run lint      # oxlint
```

Este é o único projeto do repositório com etapa de build (Vite). Os demais projetos
em `publicado/` são páginas estáticas sem build step — aqui foi necessário abrir uma
exceção porque o pedido era explicitamente React + TypeScript + Zustand + IndexedDB.

## PWA (instalável no Android)

O app é uma PWA completa: manifest próprio, ícone (192/512/maskable) e service
worker que faz cache de todos os arquivos + fontes para funcionar offline depois do
primeiro carregamento. Em HTTPS (ou `localhost`), o Chrome no Android mostra a opção
"Adicionar à tela inicial" / instala como app com ícone e janela própria, sem barra de
endereço. Sobre HTTP puro em rede local (LAN), o service worker não registra —
funciona como aba normal do navegador, sem instalação nem cache offline (limitação do
navegador, não do app: Service Worker exige contexto seguro).

## Como funciona

- **Hábitos**: crie um hábito com nome e cor, marque como feito no dia atual, veja o
  streak atual (dias seguidos) e remova quando quiser.
- **Semana**: grade com os hábitos nas linhas e os dias da semana atual nas colunas —
  clique em qualquer célula para marcar/desmarcar aquele dia específico (não só hoje).
- **Analytics**: anel de progresso com a % de hábitos concluídos hoje, gráfico de
  barras com o total de conclusões por dia (últimos 7 dias) e, por hábito, streak
  atual, recorde de streak e taxa de completude nos últimos 7 dias.
- **Tarefas da semana**: lista de afazeres avulsos (não são hábitos recorrentes),
  reiniciada a cada semana que começa.

Todos os dados (hábitos, marcações diárias, tarefas) ficam salvos no IndexedDB do
navegador. Limpar os dados do site ou trocar de navegador/dispositivo apaga/perde o
histórico — não há exportação nem backup nesta versão.

## Falta para terminar

- Sem exportação/importação de dados (backup manual, JSON, etc.) — hoje tudo vive só
  no IndexedDB do navegador.
- Sem edição de hábito depois de criado (só nome+cor na criação, sem editar meta
  semanal ainda que o campo já exista no modelo de dados).
- A grade da "Semana" mostra sempre a semana atual — não dá para navegar para semanas
  anteriores nem ver histórico em formato calendário/mês.
- Sem autenticação nem sincronização entre dispositivos — é local-first por design,
  mas isso significa um dispositivo = um histórico.
- Bundle de produção ainda não foi otimizado (single chunk ~577KB antes de gzip,
  principalmente por causa do Recharts) — aceitável para MVP, mas candidato a
  code-splitting se o projeto crescer.
- O deploy real deste projeto ainda não está integrado ao pipeline estático do
  repositório (`wrangler.toml` serve a raiz como arquivos estáticos, sem rodar build).
  Publicar em produção exige decidir entre commitar o `dist/` gerado ou configurar um
  projeto Cloudflare Pages separado com build command — isso ficou como decisão em
  aberto, não foi feito nesta sessão.
