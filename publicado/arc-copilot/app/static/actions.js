// Ações da interface que dependem do perfil: estorno/correção no RDO, equipe e documentos.
// Usa `request`, `api`, `escapeHtml`, `loadRdo` e `loadDashboard` definidos em app.js.

const ROLE_LABELS = {engineer: 'Engenheiro', master: 'Mestre de obras', worker: 'Trabalhador'};
const dialog = document.querySelector('#action-dialog');
const actionForm = document.querySelector('#action-form');
let submitHandler = null;

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function fieldRow({name, label, value = '', type = 'text', required = false, hint = ''}) {
  const input = el('input', {name, type, value, required, autocomplete: type === 'password' ? 'new-password' : 'off'});
  return el('label', {}, label, input, hint ? el('small', {className: 'hint'}, hint) : '');
}

function openDialog({title, fields, submitLabel = 'Confirmar', onSubmit}) {
  document.querySelector('#action-title').textContent = title;
  document.querySelector('#action-submit').textContent = submitLabel;
  document.querySelector('#action-fields').replaceChildren(...fields.map(fieldRow));
  document.querySelector('#action-error').hidden = true;
  submitHandler = onSubmit;
  dialog.showModal();
}

document.querySelector('#action-cancel').addEventListener('click', () => dialog.close());

actionForm.addEventListener('submit', async event => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(actionForm));
  const error = document.querySelector('#action-error');
  try {
    await submitHandler(values);
    dialog.close();
  } catch (e) {
    error.textContent = e.message;
    error.hidden = false;
  }
});

// ---- Estorno e correção de registros do RDO ----

const REASON_FIELD = {name: 'reason', label: 'Motivo (fica na auditoria)', required: true, hint: 'Mínimo de 5 caracteres'};

function reverseRecord(recordId) {
  openDialog({
    title: 'Estornar registro',
    submitLabel: 'Estornar',
    fields: [REASON_FIELD],
    onSubmit: async values => {
      await request(`${api}/records/${recordId}/reverse`, {method: 'POST', body: JSON.stringify(values)});
      await Promise.all([loadRdo(), loadDashboard()]);
    },
  });
}

function correctRecord(recordId) {
  const item = window.ARC_RDO_ITEMS[recordId];
  const isMaterial = item.type !== 'service';
  const fields = [REASON_FIELD];
  if (isMaterial) {
    fields.push(
      {name: 'quantity', label: 'Quantidade', value: item.quantity ?? '', type: 'number'},
      {name: 'unit', label: 'Unidade', value: item.unit ?? ''},
      {name: 'material_name', label: 'Material', value: item.material ?? ''},
    );
  }
  fields.push(
    {name: 'service', label: 'Serviço', value: item.service ?? ''},
    {name: 'location', label: 'Local', value: item.location ?? ''},
  );
  openDialog({
    title: 'Corrigir registro',
    submitLabel: 'Corrigir',
    fields,
    onSubmit: async values => {
      const body = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ''));
      await request(`${api}/records/${recordId}/correct`, {method: 'POST', body: JSON.stringify(body)});
      await Promise.all([loadRdo(), loadDashboard()]);
    },
  });
}

document.querySelector('#rdo-content').addEventListener('click', event => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  (button.dataset.action === 'reverse' ? reverseRecord : correctRecord)(button.dataset.record);
});

// ---- Documentos da obra (engenheiro) ----

const docForm = document.querySelector('#doc-form');
if (docForm) {
  docForm.addEventListener('submit', async event => {
    event.preventDefault();
    const result = document.querySelector('#doc-result');
    const file = document.querySelector('#doc-file').files[0];
    const body = new FormData();
    body.append('file', file);
    result.textContent = 'Indexando…';
    try {
      const response = await fetch(`${api}/documents`, {method: 'POST', body});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha ao enviar');
      const semVetor = data.chunks - data.embedded_chunks;
      result.textContent = `${data.name}: ${data.chunks} trechos, ${data.embedded_chunks} com vetor (${data.embedder})`
        + (semVetor ? `; ${semVetor} só na busca textual.` : '.');
      docForm.reset();
    } catch (e) {
      result.textContent = e.message;
    }
  });
}

// ---- Equipe (engenheiro) ----

const teamList = document.querySelector('#team-list');
let teamProjects = [];

async function loadTeam() {
  const [users, me] = await Promise.all([request('/api/users'), request('/api/me')]);
  teamProjects = me.projects;
  teamList.className = '';
  teamList.replaceChildren(...users.map(teamRow));
}

function projectChecks(selected) {
  return teamProjects.map(project => {
    const box = el('input', {type: 'checkbox', value: project.id, checked: selected.includes(project.id)});
    return el('label', {className: 'check'}, box, project.code);
  });
}

function teamRow(user) {
  const isSelf = user.id === window.ARC_USER_ID;
  const role = el('select', {name: 'role', disabled: isSelf},
    ...Object.entries(ROLE_LABELS).map(([value, text]) => el('option', {value, textContent: text, selected: value === user.role})));
  const active = el('input', {type: 'checkbox', name: 'active', checked: user.active, disabled: isSelf});
  const row = el('div', {className: 'team-row'},
    el('div', {className: 'team-id'}, el('strong', {}, user.name), el('small', {}, user.email)),
    role,
    el('label', {className: 'check'}, active, 'Ativo'),
    el('div', {className: 'team-projects'}, ...projectChecks(user.project_ids)),
    el('div', {className: 'row-actions'},
      el('button', {className: 'ghost', textContent: 'Salvar', onclick: () => saveUser(user, row)}),
      el('button', {className: 'ghost', textContent: 'Nova senha', onclick: () => resetPassword(user)})));
  return row;
}

async function saveUser(user, row) {
  const body = {
    role: row.querySelector('[name=role]').value,
    active: row.querySelector('[name=active]').checked,
    project_ids: [...row.querySelectorAll('.team-projects input:checked')].map(box => box.value),
  };
  try {
    await request(`/api/users/${user.id}`, {method: 'PATCH', body: JSON.stringify(body)});
    await loadTeam();
  } catch (e) {
    alert(e.message);
  }
}

function resetPassword(user) {
  openDialog({
    title: `Nova senha de ${user.name}`,
    submitLabel: 'Definir senha',
    fields: [{name: 'password', label: 'Nova senha', type: 'password', required: true, hint: 'Mínimo de 10 caracteres'}],
    onSubmit: values => request(`/api/users/${user.id}/password`, {method: 'POST', body: JSON.stringify(values)}),
  });
}

function newUser() {
  openDialog({
    title: 'Novo usuário',
    submitLabel: 'Criar',
    fields: [
      {name: 'name', label: 'Nome', required: true},
      {name: 'email', label: 'E-mail', type: 'email', required: true},
      {name: 'password', label: 'Senha inicial', type: 'password', required: true, hint: 'Mínimo de 10 caracteres'},
      {name: 'role', label: 'Perfil (engineer, master ou worker)', value: 'worker', required: true},
    ],
    onSubmit: async values => {
      await request('/api/users', {method: 'POST', body: JSON.stringify({...values, project_ids: [shell.dataset.projectId]})});
      await loadTeam();
    },
  });
}

const teamButton = document.querySelector('.nav-item[data-view="team"]');
if (teamButton) {
  teamButton.addEventListener('click', () => loadTeam().catch(error => { teamList.textContent = error.message; }));
  document.querySelector('#team-new').addEventListener('click', newUser);
}
