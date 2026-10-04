+--const state = { view: "dashboard", data: {}, pending: null };
const titles = {
  dashboard: "Visão geral",
  documents: "Documentos & IA",
  occurrences: "Ocorrências",
  tasks: "Tarefas",
  announcements: "Comunicados",
  reservations: "Reservas",
  contacts: "Contatos"
};
const labels = {
  occurrences: "ocorrência",
  tasks: "tarefa",
  announcements: "comunicado",
  contacts: "contato",
  spaces: "espaço",
  reservations: "reserva"
};
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = async (name, ...args) => {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api[name]) {
    throw new Error(`API method ${name} indisponível.`);
  }
  const r = await window.pywebview.api[name](...args);
  if (!r.ok) throw new Error(r.error);
  return r.data;
};

window.addEventListener("pywebviewready", load);

document.querySelectorAll("#nav button").forEach(b => b.onclick = () => show(b.dataset.view));
const todayEl = document.getElementById("today");
if (todayEl) {
  todayEl.textContent = new Intl.DateTimeFormat("pt-BR", { dateStyle: "full" }).format(new Date());
}

async function load() {
  try {
    state.data = await api("bootstrap");
    render();
  } catch (e) {
    error(e);
  }
}

function show(view) {
  state.view = view;
  document.querySelectorAll("#nav button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  const titleEl = document.getElementById("pageTitle");
  if (titleEl) titleEl.textContent = titles[view];
  render();
}

function render() {
  const fn = {
    dashboard: dashboard,
    documents: documents,
    occurrences: () => entity("occurrences"),
    tasks: () => entity("tasks"),
    announcements: () => entity("announcements"),
    contacts: () => entity("contacts"),
    reservations: reservations
  }[state.view];
  const contentEl = document.getElementById("content");
  if (contentEl && fn) contentEl.innerHTML = fn();
}

function dashboard() {
  const d = state.data.dashboard || {};
  return `
<div class="cards">
  ${metric(d.open_occurrences || 0, "Ocorrências abertas")}
  ${metric(d.overdue_tasks || 0, "Tarefas pendentes")}
  ${metric(d.upcoming_reservations || 0, "Próximas reservas")}
  ${metric(d.documents || 0, "Documentos indexados")}
</div>
<div class="grid-2">
  <div class="panel">
    <div class="panel-head">
      <h3>Ocorrências recentes</h3>
      <button class="secondary" onclick="show('occurrences')">Ver todas</button>
    </div>
    ${items(d.recent_occurrences, "title", "category")}
  </div>
  <div class="panel">
    <div class="panel-head">
      <h3>Documentos recentes</h3>
      <button class="secondary" onclick="show('documents')">Consultar</button>
    </div>
    ${items(d.recent_documents, "name", "pages", " páginas")}
  </div>
</div>`;
}

const metric = (n, l) => `
<div class="metric">
  <span>${l}</span>
  <strong>${n}</strong>
  <span>Atualizado agora</span>
</div>`;

function items(rows, titleKey, subKey, suffix = "", entityName = null) {
  if (!rows?.length) return `<div class="empty">Nenhum registro por enquanto.</div>`;
  return `<div class="list">${rows
    .map(
      r => `<div class="item">
  <div class="item-main">
    <div class="item-title">${esc(r[titleKey])}</div>
    <div class="item-sub">${esc(r[subKey])}${suffix}</div>
  </div>
  <div style="display:flex;align-items:center;gap:8px">
    ${r.status ? `<span class="badge ${esc(r.status)}">${esc(r.status)}</span>` : ""}
    ${entityName
          ? `<button class="secondary" style="padding:4px 8px;font-size:11px" onclick="removeEntityItem('${entityName}',${r.id},'${esc(r[titleKey])}')">Excluir</button>`
          : ""
        }
  </div>
</div>`
    )
    .join("")}</div>`;
}

function documents() {
  return `
<div class="toolbar">
  <div>
    <p class="eyebrow">BASE DOCUMENTAL LOCAL (RAG)</p>
    <p style="color:var(--muted);font-size:12px">PDFs e regimentos são processados no computador com rastreabilidade de fontes.</p>
  </div>
  <button class="primary" onclick="importPdf()">+ Importar PDF</button>
</div>
<div class="grid-2">
  <div class="panel">
    <h3>Pergunte aos documentos</h3>
    <div class="search">
      <input id="question" placeholder="Ex.: qual é o horário de silêncio ou regras para obras?" onkeydown="if(event.key==='Enter')ask()">
      <button class="primary" onclick="ask()">Consultar</button>
    </div>
    <div id="answer" style="margin-top:15px"></div>
  </div>
  <div class="panel">
    <div class="panel-head">
      <h3>Documentos indexados</h3>
    </div>
    <div class="list">${(state.data.documents || [])
      .map(
        d => `<div class="item">
      <div class="item-main">
        <div class="item-title">${esc(d.name)}</div>
        <div class="item-sub">${d.pages} páginas • ${esc(d.status)}</div>
      </div>
      <button class="secondary" onclick="removeDoc(${d.id},'${esc(d.name)}')">Excluir</button>
    </div>`
      )
      .join("") || '<div class="empty">Importe o primeiro PDF.</div>'
    }</div>
  </div>
</div>`;
}

async function importPdf() {
  try {
    const path = await api("choose_pdf");
    if (!path) return;
    const d = await api("import_pdf", path);
    toast(`${d.name}: ${d.pages} páginas indexadas com sucesso!`);
    await load();
    show("documents");
  } catch (e) {
    error(e);
  }
}

async function ask() {
  const inputEl = document.getElementById("question");
  const q = inputEl ? inputEl.value.trim() : "";
  if (!q) return;
  const out = document.getElementById("answer");
  if (out) out.innerHTML = '<div class="loading">Buscando evidências nos documentos...</div>';
  try {
    const r = await api("ask_documents", q);
    if (out) {
      out.innerHTML = `
<div class="answer">
  <span class="badge" style="margin-bottom:8px">${esc(r.confidence)} (${esc(r.mode || "RAG")})</span>
  <p style="margin:0">${esc(r.answer)}</p>
</div>
${(r.sources || [])
          .map(
            s => `<div class="source">
  <strong>${esc(s.document)} • pág. ${s.page}</strong>
  <p style="margin:4px 0 0">${esc(s.excerpt)}</p>
</div>`
          )
          .join("")}`;
    }
  } catch (e) {
    error(e);
  }
}

function entity(name) {
  const rows = state.data[name] || [];
  return `
<div class="toolbar">
  <p style="color:var(--muted);font-size:12px">${rows.length} registro(s)</p>
  <button class="primary" onclick="openForm('${name}')">+ Nova ${labels[name]}</button>
</div>
${items(
    rows,
    name === "contacts" ? "name" : "title",
    name === "contacts" ? "kind" : name === "tasks" ? "due_date" : name === "announcements" ? "status" : "category",
    "",
    name
  )}`;
}

function reservations() {
  const reservations = state.data.reservations || [],
    spaces = state.data.spaces || [];
  return `
<div class="toolbar">
  <p style="color:var(--muted);font-size:12px">Conflitos de horário são verificados automaticamente.</p>
  <div class="toolbar-right">
    <button class="secondary" onclick="openForm('spaces')">Gerenciar espaço</button>
    <button class="primary" onclick="openForm('reservations')">+ Nova reserva</button>
  </div>
</div>
<div class="grid-2">
  <div class="panel">
    <h3>Próximas reservas</h3>
    ${items(reservations, "title", "space_name", "", "reservations")}
  </div>
  <div class="panel">
    <h3>Espaços</h3>
    ${items(spaces, "name", "rules", "", "spaces")}
  </div>
</div>`;
}

const fields = {
  occurrences: [
    ["title", "Título", "text"],
    ["category", "Categoria", "text"],
    ["priority", "Prioridade", "select", "baixa,média,alta"],
    ["description", "Descrição", "textarea"],
    ["due_date", "Prazo", "date"],
    ["responsible", "Responsável", "text"],
    ["status", "Status", "select", "aberta,em andamento,resolvida,cancelada"]
  ],
  tasks: [
    ["title", "Título", "text"],
    ["due_date", "Prazo", "date"],
    ["responsible", "Responsável", "text"],
    ["status", "Status", "select", "pendente,em andamento,concluida"]
  ],
  announcements: [
    ["title", "Título", "text"],
    ["body", "Conteúdo", "textarea"],
    ["status", "Status", "select", "rascunho,publicado"]
  ],
  contacts: [
    ["name", "Nome", "text"],
    ["kind", "Tipo", "select", "morador,fornecedor,prestador"],
    ["phone", "Telefone", "text"],
    ["email", "E-mail", "email"],
    ["notes", "Observações", "textarea"]
  ],
  spaces: [
    ["name", "Nome do espaço", "text"],
    ["rules", "Regras", "textarea"],
    ["opens_at", "Abre às", "time"],
    ["closes_at", "Fecha às", "time"]
  ],
  reservations: [
    ["space_id", "Espaço", "spaces"],
    ["title", "Finalidade", "text"],
    ["starts_at", "Início", "datetime-local"],
    ["ends_at", "Término", "datetime-local"],
    ["notes", "Observações", "textarea"]
  ]
};

function openForm(name) {
  document.getElementById("modalKicker").textContent = `NOVA ${labels[name].toUpperCase()}`;
  document.getElementById("modalTitle").textContent = `Cadastrar ${labels[name]}`;
  document.getElementById("modalBody").innerHTML = fields[name].map(fieldHtml).join("");
  document.getElementById("modalConfirm").onclick = () => review(name);
  document.getElementById("modal").showModal();
}

function fieldHtml([key, label, type, options]) {
  if (type === "textarea") return `<div class="field"><label>${label}</label><textarea name="${key}"></textarea></div>`;
  if (type === "select")
    return `<div class="field"><label>${label}</label><select name="${key}">${options
      .split(",")
      .map(x => `<option>${x}</option>`)
      .join("")}</select></div>`;
  if (type === "spaces")
    return `<div class="field"><label>${label}</label><select name="${key}">${(state.data.spaces || [])
      .map(s => `<option value="${s.id}">${esc(s.name)}</option>`)
      .join("")}</select></div>`;
  return `<div class="field"><label>${label}</label><input name="${key}" type="${type}"></div>`;
}

async function review(entity) {
  const data = Object.fromEntries(new FormData(document.querySelector("#modal form")).entries());
  if (!Object.values(data).some(Boolean)) return;
  state.pending = { action: "create", entity, data };
  document.getElementById("confirmBody").innerHTML = `<dl>${Object.entries(data)
    .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v) || "—"}</dd>`)
    .join("")}</dl>`;
  document.getElementById("modal").close();
  document.getElementById("commitButton").onclick = commit;
  document.getElementById("confirm").showModal();
}

async function commit() {
  try {
    await api("commit", state.pending.action, state.pending.entity, state.pending.data);
    document.getElementById("confirm").close();
    toast("Ação concluída com sucesso.");
    await load();
    show(state.view);
  } catch (e) {
    error(e);
  }
}

async function removeEntityItem(entityName, id, title) {
  state.pending = { action: "delete_item", entityName, id };
  document.getElementById("confirmBody").innerHTML = `Excluir o registro <strong>${esc(title)}</strong>? Essa ação não pode ser desfeita.`;
  document.getElementById("commitButton").onclick = async () => {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_entity_item) {
        await api("delete_entity_item", entityName, id);
      } else {
        await api("commit", "delete", entityName, { id });
      }
      document.getElementById("confirm").close();
      toast("Registro excluído.");
      await load();
      show(state.view);
    } catch (e) {
      error(e);
    }
  };
  document.getElementById("confirm").showModal();
}

async function removeDoc(id, name) {
  state.pending = { action: "document_delete", id };
  document.getElementById("confirmBody").innerHTML = `Excluir o documento <strong>${esc(name)}</strong> e seu índice local? O PDF original não será apagado.`;
  document.getElementById("commitButton").onclick = async () => {
    try {
      await api("delete_document", id);
      document.getElementById("confirm").close();
      toast("Documento removido.");
      await load();
      show("documents");
    } catch (e) {
      error(e);
    }
  };
  document.getElementById("confirm").showModal();
}

async function backup() {
  try {
    const filename = await api("backup");
    toast(`Backup concluído: ${filename}`);
  } catch (e) {
    error(e);
  }
}

async function exportData() {
  try {
    const filename = await api("export_data");
    toast(`Exportação concluída: ${filename}`);
  } catch (e) {
    error(e);
  }
}

function toast(msg) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3500);
}

function error(e) {
  toast(e.message || String(e));
}
