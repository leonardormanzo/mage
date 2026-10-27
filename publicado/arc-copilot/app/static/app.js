const shell = document.querySelector('.app-shell');
const projectId = shell.dataset.projectId;
const api = `/api/projects/${projectId}`;
let activeRecordId = null;

async function request(url, options={}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json', ...(options.headers||{})}, ...options});
  if (response.status === 401) { location.href='/'; throw new Error('Sessão encerrada'); }
  const body = response.headers.get('content-type')?.includes('json') ? await response.json() : null;
  if (!response.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : JSON.stringify(body?.detail || 'Erro'));
  return body;
}

document.querySelectorAll('.nav-item').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.nav-item,.view').forEach(item => item.classList.remove('active'));
  button.classList.add('active');
  document.querySelector(`#view-${button.dataset.view}`).classList.add('active');
  if (button.dataset.view === 'rdo') loadRdo();
  if (button.dataset.view === 'materials') loadMaterials();
}));

function bubble(text, type='bot') {
  const item=document.createElement('div'); item.className=`bubble ${type}`; item.textContent=text;
  const log=document.querySelector('#chat-log'); log.appendChild(item); log.scrollTop=log.scrollHeight;
}

function confirmActions() {
  const area=document.createElement('div'); area.className='bubble actions';
  const confirm=document.createElement('button'); confirm.className='confirm'; confirm.textContent='Confirmar';
  confirm.onclick=async()=>{try{const data=await request(`${api}/records/${activeRecordId}/confirm`,{method:'POST'});bubble(data.bot);area.remove();loadDashboard();}catch(e){bubble(e.message)}};
  const cancel=document.createElement('button'); cancel.textContent='Cancelar'; cancel.onclick=()=>{bubble('Cancelamento pela interface entra na próxima iteração.');area.remove()};
  area.append(confirm,cancel); document.querySelector('#chat-log').appendChild(area);
}

document.querySelector('#chat-form').addEventListener('submit', async event => {
  event.preventDefault(); const input=document.querySelector('#chat-input'); const text=input.value.trim(); if(!text)return;
  bubble(text,'user'); input.value='';
  try {
    let data;
    if (activeRecordId) data=await request(`${api}/records/${activeRecordId}/answer`,{method:'POST',body:JSON.stringify({answer:text})});
    else data=await request(`${api}/messages`,{method:'POST',body:JSON.stringify({content:text})});
    activeRecordId=data.record_id; bubble(data.bot);
    if(data.record_status==='awaiting_confirmation') confirmActions();
    if(data.record_status==='included_in_rdo') activeRecordId=null;
  } catch(e) { bubble(e.message); }
});

async function loadDashboard(){
  const [dashboard,materials]=await Promise.all([request(`${api}/dashboard`),request(`${api}/materials`)]);
  document.querySelector('#metric-rdo').textContent=dashboard.report?.status==='closed'?'Fechado':dashboard.report?'Aberto':'—';
  document.querySelector('#metric-pending').textContent=dashboard.pending;
  document.querySelector('#metric-materials').textContent=materials.length;
  const list=document.querySelector('#recent-messages');
  list.innerHTML=dashboard.recent_messages.length?'':'<div class="empty">Nenhuma mensagem ainda.</div>';
  dashboard.recent_messages.forEach(message=>{const row=document.createElement('div');row.className='timeline-item';row.innerHTML=`<i></i><span>${escapeHtml(message.content)}</span><small>${message.status}</small>`;list.appendChild(row)});
}

async function loadMaterials(){
  const data=await request(`${api}/materials`); const grid=document.querySelector('#materials-grid');grid.innerHTML='';
  if(!data.length)grid.innerHTML='<div class="empty">Confirme um registro de material para iniciar o estoque.</div>';
  data.forEach(item=>{const card=document.createElement('article');card.innerHTML=`<span class="stock-name">${escapeHtml(item.name)}</span><strong>${item.balance} ${escapeHtml(item.unit)}</strong><small>saldo derivado das movimentações</small>`;grid.appendChild(card)});
}

async function loadRdo(){
  const data=await request(`${api}/reports/today`);const content=document.querySelector('#rdo-content');const actions=document.querySelector('#rdo-actions');actions.innerHTML='';
  if(!data.report){content.innerHTML='<div class="empty">O RDO será criado após o primeiro registro confirmado.</div>';return}
  const pending=data.pending.length?`<div class="pending-box"><strong>Pendências</strong><br>${data.pending.map(escapeHtml).join(' · ')}</div>`:'';
  content.innerHTML=pending+data.items.map(item=>`<div class="rdo-row"><div><strong>${escapeHtml(item.service||item.material||item.type)}</strong><br><small>${item.quantity??'Não informado'} ${escapeHtml(item.unit||'')}</small></div><span class="status-chip">${escapeHtml(item.status)}</span></div>`).join('');
  const pdf=document.createElement('a');pdf.className='ghost';pdf.href=`${api}/reports/${data.report.id}.pdf`;pdf.target='_blank';pdf.textContent='Gerar PDF';actions.appendChild(pdf);
  if(data.report.status==='open' && ['master','engineer'].includes(window.ARC_USER_ROLE)){const close=document.createElement('button');close.className='primary';close.textContent='Fechar RDO';close.onclick=async()=>{try{await request(`${api}/reports/${data.report.id}/close?allow_incomplete=true`,{method:'POST'});loadRdo();loadDashboard()}catch(e){alert(e.message)}};actions.appendChild(close)}
}

document.querySelector('#query-form').addEventListener('submit',async event=>{event.preventDefault();const result=document.querySelector('#query-result');result.textContent='Consultando…';try{const data=await request(`${api}/query`,{method:'POST',body:JSON.stringify({question:document.querySelector('#query-input').value})});result.className='query-result';result.innerHTML=`<p><strong>${escapeHtml(data.answer)}</strong></p><small>Rota: ${escapeHtml(data.route)} · confiança: ${Math.round(data.confidence*100)}%</small>${data.sources.map(source=>`<span class="source">${escapeHtml(source.label)}</span>`).join('')}`}catch(e){result.textContent=e.message}});
document.querySelectorAll('.refresh').forEach(button=>button.onclick=loadDashboard);
function escapeHtml(value){const div=document.createElement('div');div.textContent=String(value??'');return div.innerHTML}
loadDashboard().catch(console.error);

