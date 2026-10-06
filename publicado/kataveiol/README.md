# Kataveiol

Site de e-commerce de página única para a Kataveiol, marca de roupas femininas e
masculinas confortáveis e elegantes. Voltado para um público idoso: texto grande,
alto contraste, navegação simples e atendimento por telefone em destaque.

**Página única (HTML/CSS/JS), sem backend** — não há servidor, banco de dados,
pagamento real ou envio real de e-mail/formulário.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Estrutura

- `index.html` — página completa (HTML + CSS + JS inline, sem build step, sem
  dependências externas). Os "produtos" usam ilustrações em SVG desenhadas no
  próprio arquivo, não fotos — decisão consciente para manter o site leve e
  autocontido.

## Decisões de acessibilidade (público idoso)

- Fonte base maior que o padrão (19px) e três níveis de ajuste de texto (A / A+ / A++)
  no topo da página, salvos em `localStorage`.
- Paleta de alto contraste (texto quase preto sobre fundo claro), botões grandes
  (mínimo 48px de altura) e foco visível em todos os elementos interativos.
- Navegação reduzida a 4 itens, sem menus escondidos em hover, sem depender só de
  ícone (todo botão tem texto ou `aria-label`).
- Telefone de atendimento em destaque no topo da página — pensado para quem prefere
  resolver por voz em vez de formulário.
- Link "Pular para o conteúdo principal" para quem navega por teclado/leitor de tela.

## Carrinho e checkout

O carrinho (ícone "Sacola") funciona de verdade **no navegador**: adicionar item,
trocar tamanho, remover e ver o total são operações reais, guardadas em
`localStorage` (chave `kataveiol_cart_v1`) — sobrevivem a um recarregamento da
página, mas não existem em nenhum servidor. O botão "Finalizar Compra" é
**simulado**: mostra um aviso explicando que, em uma loja real, o próximo passo
seria o pagamento — nenhuma cobrança é feita.

## Formulário de contato

O formulário da seção "Fale com a gente" é **simulado**: ao enviar, só mostra uma
mensagem de confirmação na tela e limpa os campos — nenhum dado é transmitido para
lugar nenhum. Isso está declarado no próprio formulário (nota acima dos campos) e
aqui.

## Dados de exemplo

Telefone, e-mail e endereço da loja são placeholders, marcados no próprio site com
"(exemplo — trocar pelo real)". Produtos, preços e depoimentos são fictícios,
criados para preencher o layout com conteúdo plausível — não são peças ou clientes
reais da marca.

## Falta para terminar

- Trocar todos os dados de contato de exemplo pelos reais (telefone, e-mail,
  endereço).
- Fotos reais das peças (hoje são ilustrações SVG simples, não fotografia de
  produto).
- Se quiser vender de verdade: integrar um checkout/pagamento real (ex: Stripe,
  Mercado Pago) e um backend para pedidos — hoje é só simulação local no
  navegador.
- Se quiser que o formulário envie de verdade, integrar com um serviço de
  formulários estáticos (ex: Formspree) ou um backend simples.
- Analytics/mensuração de conversão: hoje não há nenhum (site estático sem
  backend). Para medir de verdade, adicionar GA4 ou similar antes de publicar.
