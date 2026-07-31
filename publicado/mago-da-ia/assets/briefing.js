const form = document.querySelector("#briefing-form");
const featureName = document.querySelector("#feature-name");
const featurePriority = document.querySelector("#feature-priority");
const featureList = document.querySelector("#feature-list");
const featureEmpty = document.querySelector("#feature-empty");
const addFeatureButton = document.querySelector("#add-feature");
const logoFile = document.querySelector("#logo-file");
const logoPreview = document.querySelector("#logo-preview");
const logoImage = document.querySelector("#logo-image");
const logoName = document.querySelector("#logo-name");
const resultPanel = document.querySelector("#result");
const output = document.querySelector("#brief-output");
const promptOutput = document.querySelector("#prompt-output");
const features = [];
let lastBrief = "";
let lastPrompt = "";
let lastPayload = {};

function renderFeatures() {
  featureList.querySelectorAll(".feature-item").forEach((node) => node.remove());
  featureEmpty.hidden = features.length > 0;
  features.forEach((feature, index) => {
    const row = document.createElement("div");
    row.className = "feature-item";
    row.innerHTML = `<span></span><em></em><button type="button" aria-label="Remover função">×</button>`;
    row.querySelector("span").textContent = feature.name;
    row.querySelector("em").textContent = feature.priority;
    row.querySelector("button").addEventListener("click", () => {
      features.splice(index, 1);
      renderFeatures();
    });
    featureList.appendChild(row);
  });
}

addFeatureButton.addEventListener("click", () => {
  const name = featureName.value.trim();
  if (!name) {
    featureName.focus();
    return;
  }
  features.push({ name, priority: featurePriority.value });
  featureName.value = "";
  renderFeatures();
});

featureName.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addFeatureButton.click();
  }
});

logoFile.addEventListener("change", () => {
  const file = logoFile.files[0];
  if (!file) return;
  logoName.textContent = file.name;
  logoPreview.classList.add("has-logo");
  const reader = new FileReader();
  reader.onload = () => { logoImage.src = reader.result; };
  reader.readAsDataURL(file);
});

function valuesFor(name) {
  return [...form.querySelectorAll(`[name="${name}"]:checked`)].map((field) => field.value);
}

function text(data, name) {
  return String(data.get(name) || "").trim() || "Não informado";
}

function buildBrief(event) {
  event.preventDefault();
  const data = new FormData(form);
  const types = valuesFor("tipo");
  const integrations = valuesFor("integracao");
  const featureText = features.length
    ? features.map((feature) => `- ${feature.name}: ${feature.priority}`).join("\n")
    : "- Nenhuma função adicionada";
  const selectedLogo = logoFile.files[0]?.name || "Não enviado";

  lastPayload = {
    cliente: { nome: text(data, "nome"), telefone: text(data, "telefone"), negocio: text(data, "negocio"), publico: text(data, "publico") },
    projeto: { tipos: types, problema: text(data, "problema"), resultado: text(data, "resultado"), processoAtual: text(data, "processo"), usuarios: text(data, "usuarios") },
    funcoes: features,
    integracoes: integrations,
    comercial: { orcamento: text(data, "orcamento"), prazo: text(data, "prazo"), oferta: text(data, "oferta") },
    referencias: { logo: selectedLogo, links: text(data, "referencias"), observacoes: text(data, "observacoes") }
  };

  lastBrief = `BRIEFING INICIAL — MAGO DA IA: CONSTRUÇÃO INTELIGENTE

CLIENTE
Nome: ${lastPayload.cliente.nome}
Telefone: ${lastPayload.cliente.telefone}
Empresa ou atividade: ${lastPayload.cliente.negocio}
Público atendido: ${lastPayload.cliente.publico}

PROJETO
Tipos: ${types.join(", ") || "Não selecionado"}
Problema atual: ${lastPayload.projeto.problema}
Resultado desejado: ${lastPayload.projeto.resultado}
Como funciona hoje: ${lastPayload.projeto.processoAtual}
Usuários: ${lastPayload.projeto.usuarios}

FUNÇÕES E PRIORIDADES
${featureText}

ROTINAS E INTEGRAÇÕES
${integrations.join(", ") || "Nenhuma selecionada"}

ORÇAMENTO E PRAZO
Faixa disponível: ${lastPayload.comercial.orcamento}
Prazo desejado: ${lastPayload.comercial.prazo}
Oferta de interesse: ${lastPayload.comercial.oferta}

REFERÊNCIAS
Logotipo: ${selectedLogo} — anexar separadamente ao e-mail
Links: ${lastPayload.referencias.links}
Observações: ${lastPayload.referencias.observacoes}

PRÓXIMOS PASSOS PROPOSTOS
1. Revisar o problema e as perguntas pendentes.
2. Separar escopo essencial, importante e futuro.
3. Estimar prazo e investimento por faixas.
4. Criar um protótipo demonstrativo em uma página HTML.
5. Diferenciar claramente protótipo, MVP e produção.

IMPORTANTE
Mais funções, integrações e regras aumentam análise, desenvolvimento, testes e manutenção. Este briefing não é um orçamento automático.`;

  lastPrompt = `ATUE COMO
Especialista sênior em produto digital, UX/UI e desenvolvimento front-end para empresas da construção civil.

OBJETIVO
Crie um protótipo navegável de uma única página HTML para apresentar a ideia abaixo de forma clara a uma pessoa leiga. O protótipo deve demonstrar o fluxo principal e ajudar a validar a proposta antes de qualquer desenvolvimento completo.

CONTEXTO DO CLIENTE
Empresa ou atividade: ${lastPayload.cliente.negocio}
Público atendido: ${lastPayload.cliente.publico}
Problema atual: ${lastPayload.projeto.problema}
Resultado desejado: ${lastPayload.projeto.resultado}
Como funciona hoje: ${lastPayload.projeto.processoAtual}
Usuários previstos: ${lastPayload.projeto.usuarios}
Tipo de solução considerado: ${types.join(", ") || "a definir"}

FUNÇÕES PRIORIZADAS
${featureText}

INTEGRAÇÕES DE INTERESSE
${integrations.join(", ") || "Nenhuma informada"}

DIREÇÃO VISUAL E REFERÊNCIAS
Links ou estilos: ${lastPayload.referencias.links}
Logotipo disponível: ${selectedLogo}
Observações: ${lastPayload.referencias.observacoes}

ENTREGA
- Gere um único arquivo index.html responsivo, com HTML, CSS e JavaScript no próprio arquivo.
- Apresente primeiro o problema, depois a proposta e então uma demonstração visual do fluxo principal.
- Use dados fictícios claramente identificados como demonstração.
- Inclua estados vazios, mensagens de ajuda e uma chamada para a próxima etapa.
- Escreva em português do Brasil, com linguagem simples e profissional.
- Priorize boa leitura no celular e no computador.
- Não implemente login, pagamento, banco de dados ou integrações reais nesta etapa.
- Não prometa resultados garantidos e não apresente o protótipo como produto em produção.

CRITÉRIOS DE QUALIDADE
1. A ideia principal deve ser compreendida em até 30 segundos.
2. O caminho principal deve exigir poucos cliques.
3. O visual deve combinar confiança profissional com personalidade própria.
4. Toda suposição deve aparecer em uma seção “Hipóteses para validar”.
5. Ao final, liste o que é demonstração e o que precisaria ser desenvolvido para virar um MVP.

Antes de gerar o HTML, faça no máximo cinco perguntas somente se faltar alguma informação indispensável. Caso contrário, declare as suposições e crie o protótipo.`;

  output.textContent = lastBrief;
  promptOutput.textContent = lastPrompt;
  resultPanel.classList.add("visible");
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function download(filename, content, type = "text/plain") {
  const blob = new Blob([content], { type: `${type};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

form.addEventListener("submit", buildBrief);
document.querySelector("#copy-brief").addEventListener("click", async (event) => {
  await navigator.clipboard.writeText(lastBrief);
  const original = event.currentTarget.textContent;
  event.currentTarget.textContent = "Copiado!";
  setTimeout(() => { event.currentTarget.textContent = original; }, 1500);
});
document.querySelector("#download-brief").addEventListener("click", () => download("briefing-mago-da-ia.txt", lastBrief));
document.querySelector("#download-json").addEventListener("click", () => download("briefing-mago-da-ia.json", JSON.stringify(lastPayload, null, 2), "application/json"));
document.querySelector("#copy-prompt").addEventListener("click", async (event) => {
  await navigator.clipboard.writeText(lastPrompt);
  const original = event.currentTarget.textContent;
  event.currentTarget.textContent = "Prompt copiado!";
  setTimeout(() => { event.currentTarget.textContent = original; }, 1500);
});
document.querySelector("#download-prompt").addEventListener("click", () => download("prompt-prototipo-mago-da-ia.txt", lastPrompt));
document.querySelector("#print-brief").addEventListener("click", () => window.print());
document.querySelector("#email-brief").addEventListener("click", () => {
  const subject = `Briefing inicial — ${lastPayload.cliente?.nome || "novo projeto"}`;
  const url = `mailto:leonardo.r.manzo@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lastBrief)}`;
  window.location.href = url;
});

const queryOffer = new URLSearchParams(window.location.search).get("oferta");
if (queryOffer) {
  const select = document.querySelector("#offer-select");
  if ([...select.options].some((option) => option.value === queryOffer)) select.value = queryOffer;
}
