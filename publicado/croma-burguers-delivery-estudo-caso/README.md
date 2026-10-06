# Croma Burguers Delivery — Estudo de Caso

Protótipo de página única (sem backend) para um fluxo de delivery de hambúrgueres:
cardápio filtrável, carrinho lateral com quantidade/subtotal e checkout simulado
via WhatsApp.

**Importante:** este é um estudo de caso de UI/UX, não o site oficial da
Croma Pizza & Burguers e não tem qualquer afiliação com a marca real. O
Instagram [@cromaburguers](https://www.instagram.com/cromaburguers/) e o
[linktree oficial](https://linktr.ee/cromaburguers) foram consultados apenas
como referência de contexto (rede com 4 unidades em São Paulo, modelo de
rodízio + iFood). O cardápio, os preços, as fotos (substituídas por ilustração
com emoji) e as métricas ("~32 min", "4.8/5") deste protótipo são **fictícios/
ilustrativos**, criados para este exercício — não foi extraído nenhum dado
real de cardápio ou preço da empresa.

## Como abrir

Página única, sem build e sem dependências além das fontes do Google Fonts
(Outfit + Inter, carregadas via CDN). Basta abrir `index.html` no navegador,
ou servir a pasta com `npx serve .`.

## O que funciona

- Cardápio com filtro por categoria (Burgers, Acompanhamentos, Bebidas).
- Carrinho lateral: adicionar/remover item, ajustar quantidade, subtotal,
  taxa de entrega fixa e total, tudo calculado no navegador.
- Botão "Finalizar pedido via WhatsApp" gera o texto que seria enviado e
  mostra em um modal — **nenhuma mensagem é enviada de verdade** e não há
  número de WhatsApp real embutido no código.
- Responsivo (testado em largura mobile), navegável por teclado, contraste
  verificado nos textos principais.

## Falta para terminar (se isso virasse um site real)

- Trocar as ilustrações com emoji por fotos reais do cardápio (com direito de
  uso autorizado).
- Integração real de checkout: `wa.me` com número verdadeiro da loja, ou um
  backend de pedidos de verdade (hoje é só simulação em memória do navegador).
- Cardápio e preços reais, vindos de uma fonte oficial da empresa.
- Analytics (GA4 ou equivalente) — hoje não há nenhum mecanismo de medição,
  por ser um protótipo estático sem hospedagem com tráfego real.
- Persistência do carrinho entre reloads (hoje reseta ao atualizar a página).

## Checklist de site de alto valor (10 critérios)

| # | Critério | Status |
|---|----------|--------|
| 1 | Estratégia antes do design | Atendido — objetivo único: mostrar um fluxo de delivery direto (cardápio → carrinho → checkout) sem taxa de marketplace. |
| 2 | Design autoral | Atendido — paleta e tipografia (Outfit + Inter, tons quentes neutros + laranja-queimado como único acento) definidas via `ui-ux-pro-max`, não é um template genérico. |
| 3 | Copywriting que converte | Atendido — títulos, CTAs específicos ("Finalizar pedido via WhatsApp") e textos em português, sem lorem ipsum. |
| 4 | Performance técnica | Atendido para o escopo — HTML/CSS/JS inline, sem imagens pesadas (ilustração com emoji), carregamento instantâneo. |
| 5 | SEO estrutural | Parcial — `title`/`meta description` e um único `h1` presentes; sem sitemap/dados estruturados (site de página única, não publicado). |
| 6 | Responsivo de verdade | Atendido — breakpoints para tablet/mobile, sem scroll horizontal, alvos de toque ≥44px. |
| 7 | Acessibilidade (WCAG AA) | Atendido no essencial — contraste verificado, navegação por teclado, `aria-label` em ícones, `prefers-reduced-motion` respeitado. Não passou por auditoria automatizada (Lighthouse) formal. |
| 8 | Analytics e mensuração | **Não atendido, conscientemente** — protótipo estático sem hospedagem/tráfego real, não faz sentido instrumentar analytics ainda. |
| 9 | Robustez técnica | Atendido para o tamanho do projeto — um arquivo único, mas organizado em seções claras (CSS por bloco, JS comentado por responsabilidade). |
| 10 | Segurança e infraestrutura | Atendido no que se aplica — sem credenciais, sem chamadas externas além do Google Fonts; ainda não publicado (HTTPS depende do deploy futuro). |
