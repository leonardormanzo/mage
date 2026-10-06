# Loja Cris — E-commerce

Site institucional/vitrine para a Loja Cris (moda feminina, Centro de Osasco-SP),
inspirado no perfil real [@loja__cris](https://www.instagram.com/loja__cris/) no
Instagram. Página única, sem backend: o visitante monta a sacola no site e finaliza
o pedido no grupo oficial do WhatsApp da loja.

## O que tem no site

- **Catálogo com filtro por categoria** (blusas, calças, bodys, plus size, fitness,
  acessórios), baseado nos tipos de peça e faixa de preço (R$ 25–70) observados no
  feed real do Instagram.
- **Carrinho/sacola** com quantidade por item, total calculado em tempo real.
- **Finalizar pedido**: copia um resumo formatado do pedido para a área de
  transferência e abre o grupo oficial do WhatsApp da loja, para o cliente colar e
  enviar. Não existe checkout automático nem cobrança — é a loja quem confirma
  disponibilidade e combina o pagamento, do jeito que já funciona hoje.
- Seção **"A loja"** com endereço real (Rua Natanael Tito Salmon, 147, Centro de
  Osasco) e mapa incorporado.
- Seção de depoimentos que **linka para os destaques reais do Instagram**
  ("Clientes", "Feedback") em vez de inventar avaliações falsas.
- Botão flutuante de WhatsApp e header/footer com links reais para Instagram e grupo.

Página única, sem backend, sem build step — abra `index.html` direto no navegador ou
sirva com `npx serve .`.

## Dados usados (coletados do perfil público @loja__cris)

- Nome, categoria e bio do perfil, endereço da loja física, link do grupo oficial do
  WhatsApp — todos públicos no Instagram no momento da criação do site.
- Preços e tipos de peça dos produtos do catálogo foram inspirados nos posts reais
  (ex.: "Peplum nova apenas 35,00", "Body tule plus size 44,90"), mas os **nomes e a
  lista completa de produtos são exemplos**, não um espelho exato do estoque atual.

## Falta para terminar

- **Fotos reais dos produtos**: os cards do catálogo usam ícones/gradientes como
  placeholder — não usamos as fotos do Instagram porque são conteúdo autoral da loja
  e eu não tinha autorização explícita para reaproduzi-las. Trocar por fotos reais
  (com consentimento) antes de publicar de verdade.
- **Número de WhatsApp comercial**: só o link do grupo público estava disponível.
  Se a loja tiver um número comercial dedicado (com API do WhatsApp Business), dá
  para trocar o botão "Finalizar pedido" por um link `wa.me` com a mensagem já
  preenchida automaticamente, sem depender de copiar/colar.
- **Horário de funcionamento**: não estava nas informações públicas do perfil —
  hoje o site só direciona para o WhatsApp; vale confirmar com a loja e colocar o
  horário fixo no site.
- **Estoque e preços reais**: como é site estático, os itens e preços do catálogo
  são fixos no código (`index.html`). Sem um backend/planilha conectada, atualizar
  o catálogo significa editar o arquivo à mão.
- **Analytics**: nenhum GA4/Pixel instalado ainda — se for para produção, adicionar
  para medir cliques em "Finalizar pedido".

## Critérios de site de alto valor — checklist

1. **Estratégia** ✅ — objetivo único e claro: levar o visitante da vitrine ao pedido
   pelo WhatsApp, sem distrações.
2. **Design autoral** ✅ — paleta rosa/laranja e tipografia arredondada (Baloo 2 +
   Nunito Sans) espelham a identidade visual real da marca (logo laranja com
   coração rosa), não é um template genérico.
3. **Copywriting** ✅ — textos escritos para o público real da loja, sem lorem ipsum;
   preços e nomes de peça no tom que a loja já usa nos posts.
4. **Performance** ✅ — página única, sem frameworks, sem imagens pesadas (ícones em
   SVG inline); deve carregar rápido em qualquer conexão.
5. **SEO estrutural** ✅ — `title`, `meta description`, um único `h1` na hero,
   hierarquia de headings coerente. ⚠️ Sem sitemap/dados estruturados — desnecessário
   para uma página única.
6. **Responsivo** ✅ — testado em layout mobile (menu hambúrguer, grid fluido, carrinho
   em drawer full-width no celular), sem scroll horizontal.
7. **Acessibilidade** ✅ — contraste verificado nas cores principais, `aria-label` em
   botões de ícone, foco visível, `prefers-reduced-motion` respeitado.
8. **Analytics** ❌ — não incluído neste MVP (ver "Falta para terminar").
9. **Manutenibilidade** ✅ — um arquivo `index.html` comentado por blocos (header,
   hero, catálogo, carrinho), dados de produto centralizados num array `PRODUCTS` no
   topo do `<script>`, fácil de editar sem mexer no resto.
10. **Segurança/infraestrutura** ✅ — sem segredos, sem formulário que colete dados
    sensíveis; hospedagem estática (mesmo padrão Cloudflare do resto do repo) é
    suficiente para o tráfego esperado.
