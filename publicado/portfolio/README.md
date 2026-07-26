# Portfólio — Leonardo Manzo

Página única de portfólio pessoal: apresentação, trajetória (arquiteto/gestor de obras
em transição para Engenharia de Soluções em IA) e vitrine dos projetos publicados neste
repositório.

**Página única (HTML/CSS/JS), sem backend** — tema claro/escuro com preferência salva em
`localStorage`, navegação por âncoras, revelação de seções ao rolar e um fundo fixo com
grade cinética em `<canvas>`: a grade se deforma em direção ao cursor, gera ondas ao
clicar e desliza levemente com o scroll (parallax). As cores da grade vêm das variáveis
CSS do site, então acompanham o tema claro/escuro automaticamente. Com
`prefers-reduced-motion` ativado, renderiza um único frame estático — sem loop de
animação, sem reagir ao cursor, sem ondas de clique.

Esse efeito é uma adaptação em JS puro/canvas de um componente React (`kinetic-grid.tsx`)
que o usuário forneceu como referência — portado sem framework porque o projeto é HTML
estático (sem Next.js/React/Tailwind/shadcn), então recriar o mesmo algoritmo em canvas
vanilla manteve o efeito idêntico sem mudar a arquitetura do site.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Estrutura

- `index.html` — todo o site (marcação, estilos e script).
- `assets/Leonardo-Manzo-CV.pdf` — currículo usado no botão "Baixar CV".

## Links dos projetos

Os cards de "Projetos" apontam por caminho relativo para as pastas irmãs em
`publicado/` (`vigia-obra-frontend`, `diario-de-obra`, `checklist-de-obra`) e para
`Site/Mago da IA - Home Standalone.html`. Para os links funcionarem, mantenha essa
estrutura de pastas ao publicar (ex: GitHub Pages servindo a raiz do repositório).

## Falta para terminar

- O card "Mago da IA" aponta para o HTML de demonstração em `Site/`; esse arquivo tem
  links internos quebrados (`Mago da IA - Contato.dc.html`, `Mago da IA - Demo.dc.html`,
  sobras da exportação da ferramenta original) que valem a pena corrigir antes de
  divulgar amplamente.
- O visual do herói usa um emblema ilustrativo (sem foto) — trocar por uma foto real é
  opcional, mas fica fácil: substituir o bloco `.hero-visual` por uma `<img>`.
- Sem analytics/formulário de contato com backend — contato é só por `mailto:`/`tel:` a
  propósito, para não ter um formulário "falso" que não envia nada de verdade.
