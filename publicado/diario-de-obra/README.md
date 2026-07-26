# Diário de Obra

Protótipo de interface para diário de obra: registro diário de atividades, clima,
mão de obra e ocorrências (classificadas por severidade: nenhuma / atenção /
crítica), com fluxo de rascunho → assinatura.

**Página única (HTML/CSS/JS), sem backend** — o estado vive apenas na sessão do
navegador e não persiste ao recarregar a página.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Seções

- **Diários**: registros do dia (progresso da obra, clima, atividades, mão de obra).
- **Ocorrências**: eventos fora do previsto, classificados por severidade.
- **Rascunhos / Assinados**: um diário fica como rascunho até ser assinado.
- **Configurações**: ajustes gerais do app.

## Falta para terminar

Persistência real dos dados (hoje some ao recarregar) e a assinatura em si — hoje
é só uma troca de status visual, sem validação de quem assinou.
