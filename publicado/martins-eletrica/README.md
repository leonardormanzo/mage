# Martins Elétrica

Site institucional de página única para a Martins Elétrica, empresa de instalações e
manutenções elétricas residenciais, comerciais e industriais. Apresenta os serviços,
diferenciais e um jeito de o visitante entrar em contato (WhatsApp ou formulário).

**Página única (HTML/CSS/JS), sem backend** — não há servidor, banco de dados ou envio
real de e-mail.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Estrutura

- `index.html` — página completa (HTML + CSS + JS inline, sem build step).
- `assets/logo.jpg` — logo enviada pelo cliente, usada no cabeçalho, hero e rodapé.

## Conteúdo e dados de exemplo

Os serviços listados (instalações residenciais, comerciais/industriais, manutenção e
reparos, padrão de entrada e regularização) vieram do briefing do cliente. **Telefone,
WhatsApp, e-mail, região de atendimento e horário são placeholders de exemplo**,
marcados no próprio site com a etiqueta "exemplo — trocar pelo(a) [dado] real". Antes de
publicar de verdade, é preciso substituir:

- Número de WhatsApp: variável `WHATSAPP_NUMBER` no `<script>` do `index.html` (formato
  `55DDDNUMERO`, sem espaços ou símbolos) — usada tanto no botão flutuante quanto no
  botão do topo.
- Telefone, e-mail, região e horário exibidos na seção de contato.
- Links de redes sociais no rodapé (hoje apontam para `#`).

## Formulário de contato

O formulário da seção "Peça seu orçamento" é **simulado**: ao enviar, só mostra uma
mensagem de confirmação na tela e limpa os campos — nenhum dado é transmitido para
lugar nenhum. Isso está declarado tanto no próprio formulário (nota acima dos campos)
quanto aqui. Hoje o canal real de contato é o botão de WhatsApp.

## Falta para terminar

- Trocar todos os dados de contato de exemplo pelos reais (telefone, e-mail, região,
  horário, redes sociais).
- Se quiser que o formulário envie de verdade, integrar com um serviço de formulários
  estáticos (ex: Formspree) ou um backend simples — hoje é só simulação local.
- Fotos reais de obras/serviços da empresa (o site hoje usa apenas a logo, sem galeria
  de trabalhos realizados).
