# Arquitetool — redesign de conceito

Site institucional de página única, redesign de conceito inspirado no site real
[arquitetool.com.br](https://arquitetool.com.br/) (plataforma que conecta clientes,
profissionais e fornecedores em reformas de obra). Objetivo do exercício: propor uma
direção visual mais elegante e exclusiva, voltada a um público em ascensão à classe A,
com uma abertura em parallax onde um interior totalmente acabado se **desconstrói em
camadas** conforme o visitante rola a página — acabamento → paredes → instalações →
estrutura — reforçando a mensagem "cuidamos de cada camada da sua obra".

**Página única (HTML/CSS/JS), sem backend** — não há servidor, banco de dados ou envio
real de formulário. Sem framework, sem build step.

**Importante — não afiliado.** Este projeto é um exercício de redesign para portfólio,
sem qualquer vínculo com a empresa real Arquitetool. Por isso:

- **Números da seção de estatísticas** ("+300 obras", "4,9/5,0") são **ilustrativos**,
  criados para preencher o layout — o site real exibia contadores animados sem o valor
  real acessível no momento da extração. As duas estatísticas de texto ("20% mais
  rápida", "18% de economia") são a mensagem de marketing pública do site original.
- **Depoimento** foi generalizado (sem o nome da cliente real citada no site original)
  e está marcado no próprio site como ilustrativo.
- **Galeria** usa composições gráficas abstratas (SVG), não fotografias de obras reais
  — a empresa real não teve fotos de portfólio reaproveitadas aqui.
- **Contato** (telefone, e-mail, WhatsApp) são placeholders de exemplo, marcados como
  tal, para não direcionar contato real para a empresa verdadeira a partir de um site
  não-oficial. Substituir pela variável `WHATSAPP_NUMBER` no `<script>` do
  `index.html` e pelos textos da seção `#contato` antes de qualquer uso além de
  portfólio.
- **Lista de parceiros/marcas** (Leroy Merlin, Deca, Creditas etc.) reproduz o que já é
  informação pública no site oficial da empresa, mantida como referência de contexto.
- `meta name="robots" content="noindex, nofollow"` foi deixado no `<head>` de propósito
  para não indexar este redesign de conceito em buscadores.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## O efeito de parallax (hero)

- `.hero-pin` é uma seção de `340vh` (`240vh` em telas pequenas) com `.hero-stage` fixo
  via `position: sticky`, criando uma janela de rolagem "pinada".
- Quatro camadas SVG (`layerFinish`, `layerWalls`, `layerMep`, `layerStructure`) recebem
  opacidade e transformação calculadas em JS puro a partir do progresso de rolagem
  (sem dependência externa como GSAP), com faixas de progresso escalonadas para que
  cada camada se desfaça em sequência.
- Um texto de legenda troca de frase conforme a camada ativa, narrando a
  "desconstrução" em sincronia com o scroll.
- Respeita `prefers-reduced-motion`: quando ativado, o efeito de scroll é desligado e a
  seção vira uma altura fixa sem pin, sem prejuízo de conteúdo.

## Checklist — site de alto valor (10 critérios)

| # | Critério | Status |
|---|---|---|
| 1 | Estratégia antes do design | ✅ Cada seção mapeia 1:1 para uma etapa de conversão do site real (credibilidade → prova social → CTA de contato). |
| 2 | Design autoral, não template | ✅ Paleta dark luxury (preto quente + dourado + azul-estrutura), tipografia Cinzel/Josefin Sans, hero de parallax autoral — nada de tema genérico. |
| 3 | Copywriting que converte | ✅ Textos reescritos em tom mais exclusivo; nenhum lorem ipsum. CTAs específicos ("Fale com um especialista", não "clique aqui"). |
| 4 | Performance técnica | ✅ Zero imagens externas (só SVG inline + 2 famílias de fonte via Google Fonts), JS mínimo sem libs. Não medido com Lighthouse nesta sessão — recomendo rodar antes de qualquer publicação real. |
| 5 | SEO estrutural | ⚠️ Parcial: `title`/`meta description`, único `h1` no hero, hierarquia de `h2` correta. `noindex` deixado de propósito (ver seção "não afiliado" acima) — remover se decidir publicar de verdade. |
| 6 | Responsivo de verdade | ✅ Testado com Playwright em 390px (mobile) e 1440px (desktop) — ver seção abaixo. Menu colapsa em hambúrguer <860px, sem scroll horizontal. |
| 7 | Acessibilidade (WCAG AA) | ✅ Contraste do texto principal (creme sobre preto) e do dourado testados visualmente; `skip-link`, `aria-label`/`aria-expanded` no menu, `alt`/`aria-label` na ilustração do hero, `:focus-visible` visível. |
| 8 | Analytics e mensuração | ❌ Não implementado — site estático sem backend/hospedagem definida. Se for publicar de verdade, adicionar GA4 ou Plausible. |
| 9 | Robustez técnica | ✅ Um único `index.html` organizado por blocos comentados (header, hero, seções, footer, script), sem gambiarra. |
| 10 | Segurança e infraestrutura | ✅ Estático, sem segredos, sem formulário com envio real (só link `wa.me`). HTTPS depende da hospedagem (Cloudflare, no padrão do repo). |

## Falta para terminar

- Trocar todos os placeholders (WhatsApp, telefone, e-mail, redes sociais, números da
  seção de estatísticas) pelos dados reais, se este conceito for adotado formalmente.
- Rodar um teste de Lighthouse/Core Web Vitals antes de qualquer publicação real.
- Se for publicar de fato como site institucional (não só portfólio), remover o
  `noindex` do `<head>` e revisar a seção "não afiliado" deste README.
- Fotos reais de obras/projetos, caso quiram substituir a galeria conceitual por
  portfólio de verdade.
