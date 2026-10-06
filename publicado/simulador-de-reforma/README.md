# Simulador de Reforma

Protótipo de generative design pensado para **entrar como uma seção dentro do site de uma
empresa de reforma** — quem usa é o cliente final (morador), não um engenheiro. A pessoa
informa área do apartamento, orçamento, quantos quartos tem hoje e o que é mais importante
pra ela (economizar, ganhar espaço/integração, ou sustentabilidade da obra), e recebe várias
propostas de reforma diferentes, já ranqueadas — com custo, prazo, ganho de integração e
impacto ambiental estimados de cada uma.

**Página única (HTML/CSS/JS), sem backend** — todo o cálculo roda no navegador; nada é
salvo entre recarregamentos. O botão "Falar com um especialista" no rodapé é só um mock
visual (sem link real) — ele existe para simular como a seção se encaixaria dentro do funil
comercial de um site real.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Como o gerador funciona

Cada proposta combina três decisões de projeto:

- **Nível de intervenção**: só acabamento, reforma parcial (integra dois ambientes) ou
  reforma ampla (planta bem integrada).
- **Nível de acabamento**: econômico, médio ou alto padrão.
- **Tipo de material**: convencional ou de menor impacto ambiental.
- Opcionalmente, o que fazer com um quarto sobrando (virar home office ou suíte ampliada),
  se a pessoa tiver 2+ quartos.

A partir dessas combinações, o algoritmo calcula custo total, prazo de obra (semanas),
ganho de integração dos ambientes (%) e uma pegada de carbono estimada — e ranqueia tudo
numa nota de 0 a 100, recalculada em tempo real conforme os três critérios (economia,
espaço, sustentabilidade) que a pessoa ajustar nos sliders. A planta simplificada em cada
card reflete a combinação real daquela proposta (paredes tracejadas = removidas na reforma
parcial, quase invisíveis = reforma ampla), não é um ícone genérico.

## Diferença da primeira versão deste protótipo

A primeira versão deste protótipo era voltada a construção nova (terreno, malha estrutural,
pavimentos) com visual técnico escuro, pensada para um público de engenheiros/construtoras.
Foi reformulada para reforma de apartamento existente, com linguagem simples e visual claro
e acolhedor — porque o uso real imaginado é o cliente final gerando sozinho, dentro do site
de uma empresa de reforma.

## Limites e honestidade dos números

- Custo, prazo e impacto ambiental são **estimativas de referência simplificadas**
  (constantes `INTERVENCOES`, `MATERIAIS` e `CO2_BASE_POR_M2` no início do `<script>`) —
  não vêm de uma tabela de preços real e precisam ser calibradas com dados de região e
  fornecedor antes de qualquer uso comercial.
- Não substitui visita técnica, projeto de arquitetura ou orçamento formal de uma
  construtora/arquiteto(a).
- A planta simplificada é esquemática (2 blocos sociais + quartos em fileira) — não
  representa a planta real do apartamento da pessoa.

## Falta para terminar

- Conectar o botão "Falar com um especialista" a um formulário/WhatsApp real.
- Deixar o cliente desenhar a planta real (hoje é um esquema fixo, não a planta dele).
- Exportar a proposta escolhida em PDF para levar a uma conversa com a construtora.
- Calibrar os coeficientes de custo/prazo/impacto com dados reais de obras.
