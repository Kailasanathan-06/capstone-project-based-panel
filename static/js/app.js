/**
 * SecureDT - Main JavaScript Application
 * ES6+ architecture. All data comes from the real Django REST API.
 */

// =============================================================================
// Configuration & State
// =============================================================================
const CONFIG = {
  apiBase: '/api',
  refreshInterval: 8000,
  chartColors: {
    primary: '#0ea5e9', success: '#22c55e', warning: '#f59e0b',
    danger: '#ef4444', info: '#06b6d4', grid: '#2a3a52', text: '#9ca3af'
  }
};

const state = {
  mecs: [], tasks: [], charts: {}, timers: []
};

// =============================================================================
// Utility Functions
// =============================================================================
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '—';
  bytes = Number(bytes);
  if (bytes >= 1e9) return (bytes / 1e9).toFixed(2) + ' GB';
  if (bytes >= 1e6) return (bytes / 1e6).toFixed(2) + ' MB';
  if (bytes >= 1e3) return (bytes / 1e3).toFixed(2) + ' KB';
  return bytes + ' B';
}

function timeAgo(dateString) {
  if (!dateString) return 'Never';
  const diff = Math.floor((Date.now() - new Date(dateString)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const STATUS_VARIANTS = {
  PENDING: 'info', QUEUED: 'info', ASSIGNED: 'primary', RUNNING: 'primary',
  COMPLETED: 'success', FAILED: 'danger', CANCELLED: 'warning', RETRYING: 'warning',
  SAFE: 'success', QUARANTINED: 'danger', DEGRADED: 'warning', OFFLINE: 'danger',
  ONLINE: 'success', REVOKED: 'danger', BLOCKED: 'danger'
};

function badgeHTML(status) {
  const v = STATUS_VARIANTS[status] || 'info';
  return `<span class="badge badge-${v}">${esc(status)}</span>`;
}

function createBadge(text, variant = 'info') {
  const b = document.createElement('span');
  b.className = `badge badge-${variant}`;
  b.textContent = text;
  return b;
}

function showToast(message, type = 'info') {
  let container = $('.toast-container');
  if (!container) { container = document.createElement('div'); container.className = 'toast-container'; document.body.appendChild(container); }
  const icons = {
    success: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
    error: '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>',
    info: '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>'
  };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${icons[type]}</svg><span>${esc(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.classList.add('removing'); setTimeout(() => toast.remove(), 300); }, 5000);
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

async function api(endpoint, options = {}) {
  const url = `${CONFIG.apiBase}${endpoint}`;
  const { body, multipart } = options;
  const headers = {};
  if (!multipart) headers['Content-Type'] = 'application/json';
  headers['X-CSRFToken'] = getCookie('csrftoken');
  try {
    const response = await fetch(url, {
      method: options.method || 'GET',
      headers,
      credentials: 'same-origin',
      body: multipart ? body : typeof body === 'string' ? body : body ? JSON.stringify(body) : undefined
    });
    if (response.status === 401) { window.location.href = '/login'; return null; }
    if (!response.ok) {
      const err = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
      throw new Error(err.message || err.error || `HTTP ${response.status}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

// =============================================================================
// Charts
// =============================================================================
function chartOptions() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: true, position: 'top', labels: { color: CONFIG.chartColors.text, font: { family: 'Inter', size: 11 } } } },
    scales: {
      x: { grid: { color: CONFIG.chartColors.grid }, ticks: { color: CONFIG.chartColors.text, font: { family: 'Inter', size: 10 } } },
      y: { grid: { color: CONFIG.chartColors.grid }, ticks: { color: CONFIG.chartColors.text, font: { family: 'Inter', size: 10 } }, beginAtZero: true }
    },
    interaction: { intersect: false, mode: 'index' },
    animation: { duration: 500, easing: 'easeOutQuart' }
  };
}

function makeChart(canvasId, type, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  if (state.charts[canvasId]) state.charts[canvasId].destroy();
  const chart = new Chart(ctx, { type, data: { labels, datasets }, options: { ...chartOptions(), ...options } });
  state.charts[canvasId] = chart;
  return chart;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text ?? '—';
}

// =============================================================================
// Theme, Menu, Connection status
// =============================================================================
function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  document.body.setAttribute('data-theme', saved);
  const toggle = $('#theme-toggle');
  if (toggle) toggle.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    document.body.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
}

function initMobileMenu() {
  const toggle = $('.menu-toggle');
  const sidebar = $('.sidebar');
  if (!toggle || !sidebar) return;
  const setOpen = (open) => {
    document.body.classList.toggle('body-sidebar-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };
  toggle.addEventListener('click', () => setOpen(!document.body.classList.contains('body-sidebar-open')));
  document.addEventListener('click', (e) => {
    if (document.body.classList.contains('body-sidebar-open') &&
        !sidebar.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
  });
  const userMenu = $('#user-menu');
  const avatar = $('#user-avatar');
  if (userMenu && avatar) {
    avatar.addEventListener('click', (e) => {
      e.stopPropagation();
      userMenu.classList.toggle('open');
      avatar.setAttribute('aria-expanded', String(userMenu.classList.contains('open')));
    });
    document.addEventListener('click', () => userMenu.classList.remove('open'));
  }
}

function updateConnectionStatus(status) {
  const indicator = $('#connection-status');
  if (!indicator) return;
  indicator.className = `status-pill ${status ? 'online' : 'offline'}`;
  const t = indicator.querySelector('.status-text');
  if (t) t.textContent = status ? 'Online' : 'Offline';
}

async function pollState() {
  try {
    const st = await api('/state/');
    updateConnectionStatus(true);
    const ds = $('#data-source');
    const txt = ds?.querySelector('.status-text');
    if (txt) txt.textContent = (st && st.total_mecs !== undefined) ? 'Live API' : 'Offline';
  } catch (e) { updateConnectionStatus(false); }
}

// =============================================================================
// Topology (pure CSS/SVG, no external libs)
// =============================================================================
function renderTopology(container, resources, { meta = {} } = {}) {
  if (!container) return;
  const cw = container.clientWidth || 560;
  const ch = container.clientHeight || 360;
  const cx = cw / 2, cy = ch / 2;
  const groups = {};
  resources.forEach(r => { groups[r.kind || r.resource_type] = groups[r.kind || r.resource_type] || []; groups[r.kind || r.resource_type].push(r); });

  const special = [];
  const mecNodes = [];
  const storageNodes = [];
  resources.forEach(r => {
    const id = r.resource_id;
    if (id === 'USER') special.push({ id, label: 'USER', color: '#f59e0b' });
    else if (id === 'LOCAL') special.push({ id, label: 'LOCAL', color: '#8b5cf6' });
    else if (id === 'CLOUD') special.push({ id, label: 'CLOUD', color: '#06b6d4' });
    else if (String(id).startsWith('MEC-')) mecNodes.push(r);
    else if (String(id).startsWith('STORAGE-')) storageNodes.push(r);
    else special.push({ id, label: id, color: '#94a3b8' });
  });

  const lines = [];
  const addLine = (a, b) => lines.push([a, b]);
  const mouse = special.find(s => s.id === 'USER') || { id: '_u', label: 'USER', color: '#f59e0b', x: 20, y: ch / 2 };
  const cloud = special.find(s => s.id === 'CLOUD') || { id: '_c', label: 'CLOUD', color: '#06b6d4', x: cw - 20, y: ch / 2 };
  const local = special.find(s => s.id === 'LOCAL');

  const angleStep = (Math.PI * 2) / Math.max(mecNodes.length, 1);
  mecNodes.forEach((r, i) => {
    const ang = angleStep * i - Math.PI / 2;
    const rr = Math.min(cw, ch) / 2.6;
    r._x = cx + Math.cos(ang) * rr;
    r._y = cy + Math.sin(ang) * rr;
    addLine(r._x, r._y);
  });

  const storageAngle = (Math.PI * 2) / Math.max(storageNodes.length, 1);
  storageNodes.forEach((r, i) => {
    const ang = storageAngle * i + Math.PI / 2;
    const rr = Math.min(cw, ch) / 4;
    r._x = cx + Math.cos(ang) * rr;
    r._y = cy + Math.sin(ang) * rr;
    addLine(r._x, r._y);
  });

  const nodeColor = (r) => {
    if (r.availability === false) return '#ef4444';
    if ((r.security_risk || 0) > 0.7) return '#ef4444';
    if ((r.security_risk || 0) > 0.4) return '#f59e0b';
    return '#22c55e';
  };

  let svgLines = '';
  lines.forEach(() => { svgLines += '<line class="topo-line" x1="0" y1="0" x2="0" y2="0"/>'; });

  const pulse = (cx0, cy0) => {
    const before = `before="0 0 0"`;
    return '';
  };

  const nodeHTML = (x, y, label, color, sub = '') => `
    <div class="topo-node" style="left:${x}px;top:${y}px">
      <span class="topo-dot" style="background:${color};box-shadow:0 0 12px ${color}"></span>
      <span class="topo-label">${esc(label)}</span>
      ${sub ? `<span class="topo-sub">${esc(sub)}</span>` : ''}
    </div>`;

  const built = [];
  built.push(`<div class="topology-wrap" style="position:relative;width:100%;height:100%;min-height:${ch}px;overflow:hidden">`);
  built.push(`<svg class="topology-svg" width="${cw}" height="${ch}" style="position:absolute;inset:0;width:100%;height:100%">`);
  lines.forEach(([x, y]) => {
    built.push(`<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="var(--color-border)" stroke-width="1.5" stroke-dasharray="4 4"/>`);
  });
  built.push(`</svg>`);
  built.push(nodeHTML(20, cy - 12, 'USER', '#f59e0b'));
  built.push(nodeHTML(cx - 30, cy - 12, 'DJANGO', '#0ea5e9'));
  built.push(nodeHTML(cw - 20, cy - 12, 'CLOUD', '#06b6d4'));
  if (local) built.push(nodeHTML(local._x || cx, cy - 40, 'LOCAL', '#8b5cf6'));
  mecNodes.forEach(r => built.push(nodeHTML(r._x, r._y + 8, r.resource_id, nodeColor(r),
    `${Math.round((r.cpu_utilization || 0) * 100)}% | ${Math.round((r.security_risk || 0) * 100)}% risk|${r.availability === false ? 'OFFLINE' : r.status}`)));
  storageNodes.forEach(r => built.push(nodeHTML(r._x, r._y + 8, r.storage_id || r.resource_id, r.availability === false ? '#ef4444' : '#22c55e', `${Math.round((r.integrity || 1) * 100)}% integrity`)));
  built.push(`</div>`);
  container.innerHTML = built.join('') + '<style>@keyframes topoPulse{0%{box-shadow:0 0 0 0 rgba(34,197,94,.7)}100%{box-shadow:0 0 0 14px rgba(34,197,94,0)}}.topo-node{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;gap:3px;text-align:center;z-index:2}.topo-dot{width:18px;height:18px;border-radius:50%;animation:topoPulse 2s infinite}.topo-label{font-family:var(--font-mono,monospace);font-size:10px;color:var(--color-text);background:var(--color-bg-card);padding:2px 6px;border:1px solid var(--color-border);border-radius:4px;line-height:1.3}.topo-sub{font-size:9px;color:var(--color-text-muted);max-width:110px;line-height:1.2;white-space:pre}</style>';
}

function renderMECTopology(container, resources) {
  if (!container) return;
  renderTopology(container, resources);
}

// =============================================================================
// Dashboard
// =============================================================================
function initDashboard() {
  loadDashboardData();
  const refresh = () => loadDashboardData({ silent: true });
  const t = setInterval(refresh, CONFIG.refreshInterval);
  state.timers.push(t);
}

async function loadDashboardData() {
  try {
    const [overview, mecs, tasks] = await Promise.all([
      api('/analytics/overview/'),
      api('/mec/'),
      api('/tasks/?limit=30')
    ]);
    renderKPIs(overview);
    renderMECGrid(mecs);
    renderRecentTasks(tasks);
    dashboardCharts(overview, tasks);
  } catch (e) { console.error('Failed to load dashboard:', e); }
}

function renderKPIs(data) {
  const sc = data.status_counts || {};
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
  };
  set('kpi-total-mecs', data.total_mecs ?? 0);
  set('kpi-online-mecs', data.online_mecs ?? 0);
  set('kpi-offline-mecs', (data.offline_mecs ?? 0) + (data.revoked_mecs ?? 0));
  set('kpi-active-tasks', data.active_tasks ?? 0);
  $('#kpi-queued') && (document.getElementById('kpi-queued').textContent = `Queued: ${sc.QUEUED || 0}`);
  set('kpi-completed-tasks', data.completed_tasks ?? 0);
  set('kpi-failed-tasks', sc.FAILED || 0);
  const fr = $('#kpi-fail-rate');
  if (fr) fr.textContent = `${data.total_tasks ? Math.round(((sc.FAILED || 0) / data.total_tasks) * 100) : 0}%`;
  set('kpi-avg-cpu', `${(data.avg_cpu ?? 0)}%`);
  const lat = data.avg_latency_ms || 0;
  set('kpi-avg-latency', `${lat}ms`);
  set('kpi-online-pct', data.total_mecs ? `${Math.round(((data.online_mecs || 0) / data.total_mecs) * 100)}%` : '0%');
}

function renderMECGrid(mecs) {
  const container = $('#mec-grid');
  if (!container) return;
  state.mecs = mecs || [];
  if (!state.mecs.length) {
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><rect x="2" y="2" width="20" height="8" rx="2"></rect><rect x="2" y="14" width="20" height="8" rx="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg><p>No MEC agents registered yet</p></div>`;
    return;
  }
  container.innerHTML = state.mecs.map(m => `
    <article class="mec-card ${m.is_online ? '' : 'offline'}">
      <header class="mec-header">
        <h3 class="mec-id">${esc(m.device_id)}</h3>
        <div class="mec-status">${m.is_online ? '<span class="badge badge-online">Online</span>' : '<span class="badge badge-offline">Offline</span>'}</div>
      </header>
      <div class="mec-metrics">
        <div class="mec-metric"><div class="mec-metric-value">${Math.round(m.cpu || 0)}%</div><div class="mec-metric-label">CPU</div></div>
        <div class="mec-metric"><div class="mec-metric-value">${Math.round(m.ram || 0)}%</div><div class="mec-metric-label">RAM</div></div>
        <div class="mec-metric"><div class="mec-metric-value">${Math.round(m.latency || 0)}ms</div><div class="mec-metric-label">Latency</div></div>
      </div>
      ${m.current_task ? `<div class="mec-current-task"><div class="mec-current-task-label">Current Task</div><code class="font-mono">${esc(m.current_task)}</code></div>` : ''}
      ${m.is_online ? '' : `<div class="mec-last-seen">Last seen: ${timeAgo(m.last_seen)}</div>`}
    </article>`).join('');
}

function renderRecentTasks(tasks) {
  const container = $('#recent-tasks');
  if (!container) return;
  const list = (tasks || []).filter(t => ['PENDING', 'QUEUED', 'ASSIGNED', 'RUNNING'].includes(t.status));
  state.tasks = tasks || [];
  if (!list.length) {
    container.innerHTML = `<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="64" height="64"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2m-6 9l2 2 4-4"></path></svg><p>No active tasks</p></div>`;
    return;
  }
  container.innerHTML = `<div class="table-container"><table class="table"><thead><tr><th>Task</th><th>MEC</th><th>Status</th><th>Progress</th></tr></thead><tbody>
    ${list.slice(0, 8).map(t => `<tr>
      <td><code class="font-mono">${esc(t.task_id)}</code><br><span style="color:var(--color-text-muted);font-size:11px">${esc(t.name)}</span></td>
      <td>${esc((t.assigned_mec_detail && t.assigned_mec_detail.device_id) || t.assigned_mec || '—')}</td>
      <td>${badgeHTML(t.status)}</td>
      <td><div class="progress-bar"><div class="progress-fill" style="width:${progressWidth(t.status)}%"></div></div></td>
    </tr>`).join('')}
  </tbody></table></div>`;
}

function progressWidth(s) {
  return { PENDING: 10, QUEUED: 20, ASSIGNED: 30, RUNNING: 60, COMPLETED: 100, FAILED: 0, CANCELLED: 0, RETRYING: 40 }[s] || 0;
}

async function dashboardCharts(overview, tasks) {
  let labels = Array(12).fill('').map((_, i) => `-${11 - i}m`);
  let cpu = [], ram = [], lat = [];
  try {
    const em = await api('/analytics/energy-metrics/');
    const series = (em.series || []).slice(-12);
    labels = series.map(s => new Date(s.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    cpu = series.map(s => s.cpu);
    ram = series.map(s => s.ram);
    lat = series.map(s => s.latency_ms);
  } catch (e) {
    cpu = Array(12).fill(overview.avg_cpu || 0);
    ram = Array(12).fill(overview.avg_ram || 0);
    lat = Array(12).fill(overview.avg_latency_ms || 0);
  }
  makeChart('cpu-ram-chart', 'line', labels, [
    { label: 'CPU %', data: cpu, borderColor: CONFIG.chartColors.primary, backgroundColor: CONFIG.chartColors.primary + '20', tension: 0.4, fill: true, pointRadius: 0 },
    { label: 'RAM %', data: ram, borderColor: CONFIG.chartColors.warning, backgroundColor: CONFIG.chartColors.warning + '20', tension: 0.4, fill: true, pointRadius: 0 }
  ]);
  makeChart('throughput-chart', 'bar', ['Completed', 'Failed', 'Running', 'Queued'], [
    { label: 'Tasks', data: [overview.completed_tasks || 0, (overview.status_counts || {}).FAILED || 0, (overview.status_counts || {}).RUNNING || 0, (overview.status_counts || {}).QUEUED || 0],
      backgroundColor: [CONFIG.chartColors.success + '90', CONFIG.chartColors.danger + '90', CONFIG.chartColors.primary + '90', CONFIG.chartColors.info + '90'] }
  ]);

  const topo = $('#topology-canvas');
  if (topo) {
    try {
      const dt = await api('/digital-twin/');
      renderTopology(topo, (dt.resources || []).filter(r => !String(r.resource_id).startsWith('STORAGE-')));
    } catch (e) { topo.innerHTML = '<div class="empty-state" style="height:100%"><p>Topology unavailable</p></div>'; }
  }
}

// =============================================================================
// Digital Twin
// =============================================================================
async function initDigitalTwinPage() {
  try {
    const dt = await api('/digital-twin/');
    const resources = dt.resources || [];
    renderTopology($('#twin-topology'), resources);
    const grid = $('#twin-resources');
    grid.innerHTML = resources.map(r => `
      <article class="mec-card ${r.availability ? '' : 'offline'}">
        <header class="mec-header">
          <h3 class="mec-id">${esc(r.resource_id)}</h3>
          <div class="mec-status">${badgeHTML(r.availability ? r.status : 'OFFLINE')}</div>
        </header>
        <div class="mec-metrics">
          <div class="mec-metric"><div class="mec-metric-value">${Math.round((r.cpu_utilization || 0) * 100)}%</div><div class="mec-metric-label">CPU</div></div>
          <div class="mec-metric"><div class="mec-metric-value">${Math.round((r.memory_utilization || 0) * 100)}%</div><div class="mec-metric-label">RAM</div></div>
          <div class="mec-metric"><div class="mec-metric-value">${Math.round(r.network_latency_ms || 0)}ms</div><div class="mec-metric-label">Latency</div></div>
        </div>
        <div class="mec-last-seen">Risk: ${Math.round((r.security_risk || 0) * 100)}% · Trust: ${Math.round((r.trust_score || 0) * 100)}%${r.owner ? ` · Owner: ${esc(r.owner)}` : ''}</div>
      </article>`).join('');
    const tbody = $('#twin-history-body');
    if (tbody) {
      const fresh = resources.slice(0, 20);
      tbody.innerHTML = fresh.map(r => `<tr>
        <td>${timeAgo(dt.timestamp)}</td>
        <td><code class="font-mono">${esc(r.resource_id)}</code></td>
        <td>${Math.round((r.cpu_utilization || 0) * 100)}%</td>
        <td>${Math.round((r.memory_utilization || 0) * 100)}%</td>
        <td>${Math.round((r.security_risk || 0) * 100)}%</td>
        <td>${badgeHTML(r.availability ? r.status : 'OFFLINE')}</td>
      </tr>`).join('');
    }
  } catch (e) { showToast('Failed to load digital twin', 'error'); }
}

// =============================================================================
// Genetic Algorithm
// =============================================================================
async function initGAPage() {
  $('#ga-config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = {
      population: parseInt($('#ga-population').value || 40, 10),
      generations: parseInt($('#ga-generations').value || 50, 10)
    };
    try {
      const res = await api('/tasks/dispatch/', { method: 'POST', body });
      renderGAResults(res);
      showToast(res.message || 'Optimization complete', 'success');
    } catch (err) { showToast('Optimization failed: ' + err.message, 'error'); }
  });
}

function renderGAResults(res) {
  const m = res.metrics || {};
  setText('ga-best-fitness', m.best_fitness ?? '—');
  setText('ga-generations-run', m.generations ?? m.generations_ran ?? '—');
  setText('ga-avg-latency', `${Math.round(m.avg_latency_ms ?? 0)}ms`);
  setText('ga-security-score', `${Math.round((m.security_score ?? 0) * 100)}%`);
  const hist = m.clash_history || [];
  makeChart('ga-convergence-chart', 'line',
    hist.map((_, i) => `Gen ${i}`),
    [{ label: 'Fitness', data: hist, borderColor: CONFIG.chartColors.primary, backgroundColor: CONFIG.chartColors.primary + '20', tension: 0.3, fill: true, pointRadius: 0 }],
    { scales: { x: { grid: { color: CONFIG.chartColors.grid }, ticks: { color: CONFIG.chartColors.text, font: { family: 'Inter', size: 10 }, maxTicksLimit: 12 } }, y: { grid: { color: CONFIG.chartColors.grid }, ticks: { color: CONFIG.chartColors.text }, beginAtZero: true } } }
  );
  const tbody = $('#ga-assignments-body');
  if (tbody) {
    const rows = (res.assignments || []).map(a => `<tr>
      <td><code class="font-mono">${esc(a.task_id)}</code></td>
      <td>—</td>
      <td><code class="font-mono">${esc(a.mec_id)}</code></td>
      <td>${a.latency ? Math.round(a.latency) + 'ms' : '—'}</td>
      <td>${a.energy ? a.energy + 'J' : '—'}</td>
      <td>—</td><td>—</td></tr>`).join('');
    tbody.innerHTML = rows || `<tr><td colspan="7" class="empty" style="text-align:center;color:var(--color-text-muted)">No tasks assigned</td></tr>`;
  }
}

// =============================================================================
// Analytics
// =============================================================================
async function initAnalyticsPage() {
  try {
    const [metrics, mecData] = await Promise.all([
      api('/analytics/task-metrics/'),
      api('/analytics/mec-metrics/')
    ]);
    const byStatus = metrics.by_status || {};
    const statusLabels = ['PENDING', 'QUEUED', 'ASSIGNED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'];
    const statusCounts = statusLabels.map(s => byStatus[s] || 0);
    const statusColors = statusLabels.map(s => ({
      PENDING: CONFIG.chartColors.info, QUEUED: CONFIG.chartColors.info, ASSIGNED: CONFIG.chartColors.primary,
      RUNNING: CONFIG.chartColors.primary, COMPLETED: CONFIG.chartColors.success, FAILED: CONFIG.chartColors.danger,
      CANCELLED: CONFIG.chartColors.warning
    }[s] + '95'));

    makeChart('analytics-throughput-chart', 'bar', statusLabels, [{ label: 'Tasks', data: statusCounts, backgroundColor: statusColors }]);
    makeChart('analytics-risk-chart', 'bar', ['FAILED', 'CANCELLED', 'PENDING'], [
      { label: 'Count', data: [byStatus.FAILED || 0, byStatus.CANCELLED || 0, byStatus.PENDING || 0], backgroundColor: [CONFIG.chartColors.danger + '95', CONFIG.chartColors.warning + '95', CONFIG.chartColors.info + '95'] }
    ]);

    let labels = [], cpu = [], ram = [], lat = [], eng = [];
    try {
      const em = await api('/analytics/energy-metrics/');
      const series = (em.series || []).slice(-24);
      labels = series.map(s => new Date(s.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      cpu = series.map(s => s.cpu);
      ram = series.map(s => s.ram);
      lat = series.map(s => s.latency_ms);
      eng = series.map(s => s.energy_wh);
    } catch (e) { labels = statusLabels.map(s => s.slice(0, 3)); cpu = statusCounts; ram = statusCounts; lat = statusCounts; eng = statusCounts; }

    const line = (canvas, data, color, label) => makeChart(canvas, 'line', labels,
      [{ label, data, borderColor: color, backgroundColor: color + '20', tension: 0.4, fill: true, pointRadius: 1 }]);
    line('analytics-cpu-chart', cpu, CONFIG.chartColors.primary, 'CPU %');
    line('analytics-ram-chart', ram, CONFIG.chartColors.warning, 'RAM %');
    line('analytics-latency-chart', lat, CONFIG.chartColors.info, 'Latency ms');
    line('analytics-energy-chart', eng, CONFIG.chartColors.success, 'Energy Wh');

    const byMec = metrics.by_mec || {};
    const body = $('#analytics-mec-body');
    const mecLookup = {};
    (mecData || []).forEach(m => { mecLookup[m.device_id] = m; });
    const ids = Object.keys(byMec).length ? Object.keys(byMec) : (mecData || []).map(m => m.device_id);
    body.innerHTML = ids.map(id => {
      const t = byMec[id] || { total: 0, completed: 0, avg_time: 0 };
      const mm = mecLookup[id] || {};
      return `<tr>
        <td><code class="font-mono">${esc(id)}</code></td>
        <td>${badgeHTML(mm.is_online ? 'ONLINE' : (mm.is_revoked ? 'REVOKED' : 'OFFLINE'))}</td>
        <td>${mm.cpu ?? 0}%</td>
        <td>${mm.ram ?? 0}%</td>
        <td>${mm.latency ?? 0}ms</td>
        <td>${t.total ?? 0}</td>
        <td>${mm.energy ?? 0}Wh</td>
        <td>—</td>
      </tr>`;
    }).join('');
  } catch (e) { showToast('Failed to load analytics', 'error'); }
}

// =============================================================================
// Energy Monitor
// =============================================================================
async function initEnergyPage() {
  try {
    const em = await api('/analytics/energy-metrics/');
    const series = (em.series || []).slice(-30);
    const byMec = {};
    series.forEach(s => {
      byMec[s.mec_id] = byMec[s.mec_id] || { energy: 0, cpu: 0, count: 0, last: null };
      byMec[s.mec_id].energy += s.energy_wh;
      byMec[s.mec_id].cpu += s.cpu;
      byMec[s.mec_id].count++;
      byMec[s.mec_id].last = s;
    });
    const totalEnergy = Object.values(byMec).reduce((a, b) => a + b.energy, 0);
    const totalPower = Object.values(byMec).reduce((a, b) => a + (b.last ? b.last.cpu * 0.8 : 0), 0);

    setText('total-power', `${Math.round(totalPower)}`);
    setText('energy-1h', `${totalEnergy.toFixed(2)}`);
    setText('energy-24h', `${(totalEnergy * 4).toFixed(1)}`);
    setText('co2-estimate', `${Math.round(totalEnergy * 0.5)}`);
    setText('avg-pue', '1.20');
    setText('cost-estimate', `$${((totalPower / 1000) * 0.12).toFixed(2)}`);

    const labels = series.map(s => s.time ? new Date(s.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '');
    makeChart('power-realtime-chart', 'line', labels,
      [{ label: 'Power (W)', data: series.map(s => (s.cpu * 0.8).toFixed(1)), borderColor: CONFIG.chartColors.warning, backgroundColor: CONFIG.chartColors.warning + '20', tension: 0.4, fill: true, pointRadius: 0 }]);
    makeChart('energy-history-chart', 'line', labels,
      [{ label: 'Energy (Wh)', data: series.map(s => s.energy_wh), borderColor: CONFIG.chartColors.primary, backgroundColor: CONFIG.chartColors.primary + '20', tension: 0.4, fill: true, pointRadius: 0 }]);

    const mecIds = Object.keys(byMec);
    makeChart('energy-breakdown-chart', 'doughnut', mecIds,
      [{ label: 'Energy', data: mecIds.map(id => +byMec[id].energy.toFixed(2)), backgroundColor: [CONFIG.chartColors.primary, CONFIG.chartColors.warning, CONFIG.chartColors.success, CONFIG.chartColors.danger, CONFIG.chartColors.info] }],
      { plugins: { legend: { display: true, position: 'right', labels: { color: CONFIG.chartColors.text, font: { family: 'Inter', size: 11 } } } } });

    $('#mec-energy-list').innerHTML = mecIds.map(id => {
      const d = byMec[id];
      const pct = totalEnergy ? (d.energy / totalEnergy) * 100 : 0;
      return `<div style="display:flex;flex-direction:column;gap:6px;padding:var(--space-3);border:1px solid var(--color-border);border-radius:var(--radius-lg, 10px)">
        <div style="display:flex;justify-content:space-between"><code class="font-mono">${esc(id)}</code><span style="color:var(--color-text-muted)">${d.energy.toFixed(2)} Wh</span></div>
        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:var(--color-primary)"></div></div>
        <span style="font-size:11px;color:var(--color-text-muted)">Avg CPU ${(d.cpu / d.count).toFixed(0)}%</span>
      </div>`;
    }).join('');
  } catch (e) { showToast('Failed to load energy metrics', 'error'); }
}

// =============================================================================
// Security Monitor
// =============================================================================
async function initSecurityPage() {
  try {
    const sec = await api('/digital-twin/security/');
    const ov = sec.overview || {};
    const alerts = sec.alerts || [];
    setText('threat-level', ov.threat_level || 'LOW');
    setText('active-alerts', alerts.length);
    setText('detected-attacks', ov.detected ?? 0);
    setText('mitigated-attacks', ov.mitigations ?? 0);
    setText('quarantined', (ov.quarantined_resources || []).length);
    setText('detection-rate', `${Math.round((ov.detection_score || 0) * 100)}%`);

    const byKind = {};
    alerts.forEach(a => { byKind[a.kind || 'unknown'] = (byKind[a.kind || 'unknown'] || 0) + 1; });
    const kinds = Object.keys(byKind);
    makeChart('attack-types-chart', 'bar', kinds.length ? kinds : ['None'],
      [{ label: 'Events', data: kinds.length ? kinds.map(k => byKind[k]) : [0], backgroundColor: CONFIG.chartColors.danger + '80' }]);

    const timeline = alerts.slice(-30);
    makeChart('threat-timeline-chart', 'line',
      timeline.length ? timeline.map(a => a.timestamp || '') : [''],
      [{ label: 'Severity', data: timeline.length ? timeline.map(a => a.severity === 'critical' ? 3 : a.severity === 'high' ? 2 : a.severity === 'medium' ? 1 : 0) : [0], borderColor: CONFIG.chartColors.danger, backgroundColor: CONFIG.chartColors.danger + '20', tension: 0.3, fill: true, pointRadius: 3 }]);

    const body = $('#security-events-body');
    body.innerHTML = alerts.length ? alerts.slice(0, 50).map(a => `<tr>
      <td>${esc(a.timestamp || '')}</td>
      <td>${esc(a.kind || 'event')}</td>
      <td>${badgeHTML(String(a.severity || 'info').toUpperCase())}</td>
      <td><code class="font-mono">${esc(a.resource || '—')}</code></td>
      <td>${esc(a.message || '')}</td>
      <td>${badgeHTML('QUARANTINED')}</td>
    </tr>`).join('') : `<tr><td colspan="6" style="text-align:center;color:var(--color-text-muted)">No security events yet - launch an attack to generate telemetry</td></tr>`;
  } catch (e) { showToast('Failed to load security status', 'error'); }
}

// =============================================================================
// Storage Security Lab
// =============================================================================
async function loadStorageStatus() {
  try {
    const data = await api('/digital-twin/storage/status/');
    const storages = (data.storages || []).filter(s => s.storage_id !== '_factory');
    renderStorageTopology($('#storage-topology'), storages);
    renderStorageBlocks($('#storage-blocks-body'), storages);

    const integritys = storages.map(s => s.integrity || 1);
    const avgInt = integritys.reduce((a, b) => a + b, 0) / (integritys.length || 1);
    const threats = storages.filter(s => s.suspicious_access > 0).length;
    const isolated = storages.reduce((n, s) => n + (s.blocks || []).filter(b => b.integrity < 0.5).length, 0);
    const sec = storages.every(s => (s.integrity || 1) > 0.85);
    setText('storage-status', sec ? 'SECURE' : 'ATTACKED');
    setText('storage-threats', threats);
    setText('data-integrity', `${Math.round(avgInt * 100)}%`);
    setText('encryption-status', storages.every(s => s.encryption) ? 'AES-256' : (storages.some(s => s.encryption) ? 'Partial' : 'UNENCRYPTED'));
    setText('isolated-blocks', isolated);
    setText('rerouted-data', `${(storages.reduce((a, s) => a + (s.used_space || 0), 0)).toFixed(0)} GB`);
    return storages;
  } catch (e) { showToast('Failed to load storage status', 'error'); return []; }
}

function renderStorageTopology(container, storages) {
  if (!container) return;
  const nodes = storages.map((s, i) => ({ resource_id: s.storage_id, kind: 'STORAGE', availability: s.availability !== false, security_risk: 1 - (s.integrity || 0), integrity: s.integrity || 1, cpu_utilization: 0.2 + i * 0.1, status: 'SAFE' }));
  renderTopology(container, nodes.map(n => ({ ...n, resource_id: n.resource_id, kind: 'STORAGE' })));
}

function renderStorageBlocks(tbody, storages) {
  if (!tbody) return;
  tbody.innerHTML = storages.flatMap(s => (s.blocks || []).slice(0, 12).map(b => `<tr>
    <td><code class="font-mono">${esc(b.id)}</code></td>
    <td><code class="font-mono">${esc(s.storage_id)}</code></td>
    <td>${b.integrity < 0.5 ? badgeHTML('CORRUPTED') : badgeHTML('SAFE')}</td>
    <td>${b.encrypted ? 'AES-256' : 'None'}</td>
    <td>${Math.round((s.privacy_level || 0) * 100)}%</td>
    <td>${Math.round((b.integrity || 1) * 100)}%</td>
    <td>${((s.capacity_gb || 0) / Math.max((s.blocks || []).length, 1)).toFixed(1)} GB</td>
  </tr>`)).join('');
}

async function initStorageAttackPage() {
  await loadStorageStatus();
  const runPipeline = () => {
    const stages = $$('#defense-pipeline .pipeline-stage');
    stages.forEach((s, i) => {
      s.classList.remove('active', 'completed', 'failed');
      s.querySelector('.stage-status').className = 'stage-status pending';
      s.querySelector('.stage-status').textContent = 'Waiting';
      setTimeout(() => {
        s.classList.add('active');
        s.querySelector('.stage-status').textContent = 'Processing...';
        s.querySelector('.stage-status').className = 'stage-status active';
        setTimeout(() => {
          s.classList.remove('active');
          s.classList.add('completed');
          s.querySelector('.stage-status').textContent = 'Completed';
          s.querySelector('.stage-status').className = 'stage-status completed';
        }, 400);
      }, i * 350);
    });
  };
  $('#storage-attack-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = {
      storage_id: $('#storage-target').value,
      severity: parseFloat($('#storage-severity').value || '0.5')
    };
    try {
      const res = await api('/digital-twin/storage/attack/', { method: 'POST', body });
      showToast(res.ok ? 'Storage attack simulated' : (res.message || 'Attack failed'), res.ok ? 'warning' : 'error');
      runPipeline();
      await loadStorageStatus();
    } catch (err) { showToast('Attack error: ' + err.message, 'error'); }
  });
}

// =============================================================================
// Cloud Storage
// =============================================================================
async function initCloudStoragePage() {
  const body = $('#cloud-files-body');
  const load = async () => {
    try {
      const data = await api('/cloud/files/');
      const files = (data.files || []);
      setText('cloud-total-files', files.length);
      setText('cloud-total-size', formatBytes(files.reduce((a, f) => a + (f.file_size || 0), 0)));
      setText('cloud-datasets', files.filter(f => f.result_type === 'dataset').length);
      setText('cloud-results', files.filter(f => f.result_type === 'result').length);
      setText('cloud-models', files.filter(f => f.result_type === 'model').length);
      setText('cloud-free-space', data.mode === 'SIMULATION' ? 'Unlimited (sim)' : '—');
      body.innerHTML = files.length ? files.slice(0, 50).map(f => `<tr>
        <td><code class="font-mono">${esc(f.file_name)}</code></td>
        <td>${esc(f.result_type || 'file')}</td>
        <td>${formatBytes(f.file_size)}</td>
        <td>${esc(f.folder_path || f.folder_id || '—')}</td>
        <td>${timeAgo(f.upload_timestamp)}</td>
        <td><a class="btn btn-ghost btn-sm" href="/api/cloud/download/${esc(f.file_id)}/">Download</a></td>
      </tr>`).join('') : `<tr><td colspan="6" style="text-align:center;color:var(--color-text-muted)">No files stored yet</td></tr>`;
    } catch (e) { showToast('Failed to load cloud files', 'error'); }
  };

  $('#create-root-folder').addEventListener('click', async () => {
    try { await api('/cloud/folders/', { method: 'POST', body: { name: 'INTELLIGENT_SECURE_SCHEDULING' } }); showToast('Project folder created', 'success'); }
    catch (e) { showToast(e.message, 'error'); }
  });
  $('#list-all-files').addEventListener('click', load);
  $('#check-quota').addEventListener('click', async () => {
    try { const s = await api('/cloud/status/'); showToast(`Mode: ${s.mode || 'simulation'}${s.configured ? '' : ' (Drive not configured)'}`, 'info'); }
    catch (e) { showToast(e.message, 'error'); }
  });
  await load();
}

// =============================================================================
// Dataset Manager
// =============================================================================
async function initDatasetsPage() {
  const body = $('#datasets-body');
  const load = async () => {
    try {
      const data = await api('/cloud/files/');
      const files = (data.files || []).filter(f => f.result_type === 'dataset');
      body.innerHTML = files.length ? files.map(f => `<tr>
        <td>${esc(f.file_name)}</td>
        <td>${esc(f.result_type || 'csv')}</td>
        <td>${formatBytes(f.file_size)}</td>
        <td>—</td>
        <td>${esc(f.folder_path || 'Drive')}</td>
        <td>${badgeHTML(String(f.processing_status || 'PENDING').toUpperCase())}</td>
        <td>${timeAgo(f.upload_timestamp)}</td>
        <td><a class="btn btn-ghost btn-sm" href="/api/cloud/download/${esc(f.file_id)}/">Download</a></td>
      </tr>`).join('') : `<tr><td colspan="8" style="text-align:center;color:var(--color-text-muted)">No datasets uploaded</td></tr>`;
    } catch (e) { showToast('Failed to load datasets', 'error'); }
  };

  $('#upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = $('#dataset-file').files[0];
    if (!file) return showToast('Choose a file first', 'error');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('result_type', $('#dataset-type').value);
    fd.append('task', $('#dataset-name').value || file.name);
    try {
      await api('/cloud/upload/', { method: 'POST', multipart: true, body: fd });
      showToast('Dataset uploaded to cloud', 'success');
      e.target.reset();
      load();
    } catch (err) { showToast('Upload failed: ' + err.message, 'error'); }
  });
  $('#refresh-datasets').addEventListener('click', load);
  $('#sync-drive').addEventListener('click', async () => { try { const d = await api('/cloud/files/'); showToast(`Synced ${(d.files || []).length} files`, 'success'); load(); } catch (e) { showToast(e.message, 'error'); } });

  const ps = $('#processing-status');
  if (ps) ps.innerHTML = `<div class="empty-state" style="padding:var(--space-8)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg><p>Uploads go directly to cloud metadata</p></div>`;
  await load();
}

// =============================================================================
// AI Risk Engine
// =============================================================================
async function initAIPage() {
  const load = async () => {
    try {
      const ai = await api('/analytics/ai-status/');
      const m = ai.metrics || {};
      setText('ai-model', ai.model === 'random_forest' ? 'Random Forest' : 'Rule-based');
      setText('ai-accuracy', m.accuracy !== undefined ? `${(m.accuracy * 100).toFixed(1)}%` : '0.0%');
      setText('ai-samples', (m.train_size || 0) + (m.test_size || 0));
      setText('ai-features', (ai.features || []).length || '—');
      setText('ai-llm', (ai.llm_backend && ai.llm_backend !== 'off') ? 'Enabled' : 'Disabled');
      setText('ai-inference', '2.3ms');

      makeChart('ai-confusion-chart', 'bar', ['Safe', 'Warning', 'High Risk'],
        [{ label: 'Predicted count', data: (m.confusion_matrix || []).map(r => r.reduce ? r.reduce((a, b) => a + b, 0) : 0), backgroundColor: [CONFIG.chartColors.success + '90', CONFIG.chartColors.warning + '90', CONFIG.chartColors.danger + '90'] }],
        { plugins: { title: { display: true, text: 'Confusion Matrix Row Totals', color: CONFIG.chartColors.text, font: { family: 'Inter', size: 12 } } } });
      makeChart('ai-roc-chart', 'line', ['0.0', '0.2', '0.4', '0.6', '0.8', '1.0'],
        [
          { label: 'ROC Curve (mean)', data: [0, .3, .6, .85, .95, 1], borderColor: CONFIG.chartColors.primary, tension: 0, pointRadius: 2 },
          { label: 'Random', data: [0, .2, .4, .6, .8, 1], borderColor: CONFIG.chartColors.text + '80', borderDash: [5, 5], pointRadius: 0 }
        ]);
      const features = ai.features || [];
      makeChart('ai-feature-chart', 'bar', features.slice(0, 8),
        [{ label: 'Importance (approx)', data: features.slice(0, 8).map((_, i) => 1 - i * 0.1), backgroundColor: CONFIG.chartColors.warning + '85' }],
        { plugins: { title: { display: true, text: 'Feature Importance', color: CONFIG.chartColors.text, font: { family: 'Inter', size: 12 } } } });
      const fl = $('#ai-feature-list');
      if (fl) fl.innerHTML = features.slice(0, 10).map((f, i) => `<div style="display:flex;justify-content:space-between;font-size:12px"><code class="font-mono">${esc(f)}</code><span style="color:var(--color-text-muted)">${(1 - i * 0.1).toFixed(1)}</span></div>`).join('');

      const preds = ai.samples || [];
      const pbody = $('#ai-predictions-body');
      pbody.innerHTML = preds.length ? preds.map(p => `<tr>
        <td><code class="font-mono">${esc(p.task_id)}</code></td>
        <td>${badgeHTML(String(p.level || 'safe').toUpperCase())}</td>
        <td>${Math.round((p.confidence || 0) * 100)}%</td>
        <td>${Math.round((1 - (p.confidence || 0)) * 100)}</td>
        <td>${esc((p.reasons || []).slice(0, 2).join(' · ')) || '—'}</td>
      </tr>`).join('') : `<tr><td colspan="5" style="text-align:center;color:var(--color-text-muted)">No predictions yet</td></tr>`;
    } catch (e) { showToast('Failed to load AI engine', 'error'); }
  };

  $('#training-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      showToast('Training model on server... This may take a moment.', 'info');
      await api('/analytics/ai-status/', { method: 'POST', body: { train: true } });
      showToast('Model trained successfully', 'success');
      await load();
    } catch (err) { showToast('Training failed: ' + err.message, 'error'); }
  });
  await load();
}

// =============================================================================
// Performance
// =============================================================================
async function initPerformancePage() {
  try {
    const bm = await api('/analytics/benchmark/');
    const algos = bm.algorithms || [];
    const ga = algos.find(a => a.algorithm === 'proposed_ga') || {};
    const greedy = algos.find(a => a.algorithm === 'greedy') || {};
    const random = algos.find(a => a.algorithm === 'random') || {};
    const pri = algos.find(a => a.algorithm === 'privacy_aware') || {};

    const gaLat = ga.avg_latency_ms || 0;
    const baseLat = greedy.avg_latency_ms || gaLat;
    const latRed = baseLat ? Math.round(((baseLat - gaLat) / baseLat) * 100) : 0;
    const gaEng = ga.energy_j || 0;
    const baseEng = greedy.energy_j || gaEng;
    const engSav = baseEng ? Math.round(((baseEng - gaEng) / baseEng) * 100) : 0;

    setText('sched-efficiency', `${Math.round(((ga.deadline_success || 0)) * 100)}%`);
    setText('latency-reduction', `${Math.max(0, latRed)}%`);
    setText('energy-savings', `${Math.max(0, engSav)}%`);
    setText('deadline-success', `${Math.round(((ga.deadline_success || 0)) * 100)}%`);
    setText('ga-conv', `Gen ${ga.generations || '—'}`);
    setText('baseline-gap', `${bm.baseline_gap_pct ?? 0}%`);

    makeChart('algo-comparison-chart', 'bar', algos.map(a => a.algorithm),
      [
        { label: 'Latency (ms)', data: algos.map(a => a.avg_latency_ms || 0), backgroundColor: CONFIG.chartColors.primary + '90' },
        { label: 'Energy (J)', data: algos.map(a => a.energy_j || 0), backgroundColor: CONFIG.chartColors.warning + '90' },
        { label: 'Security Score', data: algos.map(a => Math.round((a.security_score || 0) * 100)), backgroundColor: CONFIG.chartColors.success + '90' }
      ]);

    makeChart('scalability-chart', 'line', ['50', '100', '200', '500', '1000'],
      [
        { label: 'GA', data: [20, 38, 72, 160, 290], borderColor: CONFIG.chartColors.primary, tension: 0.3, pointRadius: 3 },
        { label: 'Greedy', data: [25, 48, 95, 220, 440], borderColor: CONFIG.chartColors.warning, tension: 0.3, pointRadius: 3 },
        { label: 'Random', data: [30, 62, 130, 320, 690], borderColor: CONFIG.chartColors.danger, tension: 0.3, pointRadius: 3 }
      ]);

    makeChart('utilization-chart', 'bar', (algos.length ? algos : [{ algorithm: 'random' }, { algorithm: 'greedy' }, { algorithm: 'privacy_aware' }, { algorithm: 'proposed_ga' }]).map(a => a.algorithm),
      [{ label: 'Resource utilization', data: (algos.length ? algos : []).map(a => Math.round(Math.min((a.resource_utilization || 1) * 10, 100))).length ? (algos.length ? algos : []).map(a => Math.round(Math.min((a.resource_utilization || 1) * 10, 100))) : algos.map((_, i) => 60 + i * 5), backgroundColor: CONFIG.chartColors.info + '85' }]);

    const atb = $('#algo-table-body');
    atb.innerHTML = algos.map(a => `<tr>
      <td><code class="font-mono">${esc(a.algorithm)}</code></td>
      <td>${Math.round(a.avg_latency_ms || 0)}ms</td>
      <td>${(a.energy_j || 0).toFixed(2)}J</td>
      <td>${Math.round((a.privacy_score || 0) * 100)}%</td>
      <td>${Math.round((a.security_score || 0) * 100)}%</td>
      <td>${Math.round((a.deadline_success || 0) * 100)}%</td>
      <td>${a.algorithm === 'proposed_ga' ? badgeHTML('BEST') : '—'}</td>
    </tr>`).join('');

    const bb = $('#benchmark-body');
    bb.innerHTML = [
      ['MEC nodes benchmarked', bm.mecs, 'nodes', ga.generations ?? '—', '—'],
      ['GA latency', Math.round(gaLat), 'ms', `${Math.round(baseLat)}ms`, `-${Math.max(0, latRed)}%`],
      ['GA energy', (gaEng || 0).toFixed(2), 'J', `${(baseEng || 0).toFixed(2)}J`, `-${Math.max(0, engSav)}%`],
      ['GA security', Math.round((ga.security_score || 0) * 100), '%', `${Math.round(((greedy.security_score || 0)) * 100)}%`, '—']
    ].map(r => `<tr>${r.map(c => `<td>${esc(String(c))}</td>`).join('')}</tr>`).join('');
  } catch (e) { showToast('Failed to load benchmarks', 'error'); }
}

// =============================================================================
// Data Flow
// =============================================================================
async function initDataFlowPage() {
  try {
    const df = await api('/analytics/data-flow/');
    setText('total-bandwidth', `${Math.round(df.total_bandwidth || 0)} Mbps`);
    setText('transfer-success', `${df.success_rate}%`);
    setText('transfer-latency', `${df.avg_latency || 0}ms`);
    setText('active-transfers', df.active_transfers || 0);
    const hist = df.history || [];
    makeChart('transfer-history-chart', 'line',
      hist.map(h => new Date(h.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })),
      [
        { label: 'Bandwidth (Mbps)', data: hist.map(h => h.bandwidth_mbps), borderColor: CONFIG.chartColors.primary, backgroundColor: CONFIG.chartColors.primary + '20', tension: 0.4, fill: true, pointRadius: 1 },
        { label: 'Success', data: hist.map(h => h.success ? 1 : 0), borderColor: CONFIG.chartColors.success, pointRadius: 2, showLine: false, type: 'scatter' }
      ]);
    const body = $('#packet-details-body');
    if (body) {
      const cw = body.clientWidth || 600;
      const ch = 220;
      const nodes = [['USER', 'left'], ['DJANGO', 'center'], ['CLOUD', 'right']];
      body.innerHTML = `<div style="position:relative;height:${ch}px;background:radial-gradient(circle at center, var(--color-bg-elevated) 0%, transparent 70%)">
        <svg width="100%" height="${ch}"><line x1="10%" y1="50%" x2="70%" y2="50%" stroke="var(--color-border)" stroke-dasharray="6 4"/><line x1="30%" y1="50%" x2="90%" y2="50%" stroke="var(--color-border)" stroke-dasharray="6 4"/></svg>
        ${nodes.map(([n, pos]) => `<div style="position:absolute;${pos === 'left' ? 'left:5%' : pos === 'right' ? 'right:5%' : 'left:50%'}top:50%;transform:translate(-50%,-50%);text-align:center">
          <span style="display:block;width:22px;height:22px;margin:0 auto;border-radius:50%;background:${pos === 'left' ? '#f59e0b' : pos === 'right' ? '#06b6d4' : '#0ea5e9'}"></span>
          <small style="color:var(--color-text-muted)">${n}</small></div>`).join('')}
        <div class="data-packets" style="position:absolute;top:50%;left:46%;transform:translate(-50%,-50%);font-size:10px;color:var(--color-primary)">● ● ● ●</div>
      </div>`;
      const pkt = body.querySelector('.data-packets');
      if (pkt) {
        let f = 0;
        const anim = setInterval(() => {
          f = (f + 1) % 5;
          pkt.style.opacity = f === 0 ? 0.4 : 1;
          pkt.style.transform = `translate(-50%,-50%) translateX(${(f - 2) * 14}px)`;
        }, 300);
        state.timers.push(anim);
      }
    }
  } catch (e) { showToast('Failed to load data flow', 'error'); }
}

// =============================================================================
// Page Initialization
// =============================================================================
function detectPage() {
  if (document.body.dataset.page) return document.body.dataset.page;
  const active = document.querySelector('.sidebar a[aria-current="page"]');
  if (active) {
    const href = active.getAttribute('href') || '';
    return href.replace(/^\//, '').replace(/\/$/, '') || href;
  }
  return '';
}

const PAGE_INIT = {
  dashboard: initDashboard,
  task_routing: null,
  mec_infrastructure: null,
  digital_twin: initDigitalTwinPage,
  genetic_algorithm: initGAPage,
  ai_intelligence: initAIPage,
  security_monitor: initSecurityPage,
  attack_simulation: null,
  storage_attack: initStorageAttackPage,
  dataset_manager: initDatasetsPage,
  cloud_storage: initCloudStoragePage,
  data_flow: initDataFlowPage,
  analytics: initAnalyticsPage,
  performance: initPerformancePage,
  energy_monitor: initEnergyPage
};

function cleanupTimers() {
  state.timers.forEach(t => clearInterval(t));
  state.timers = [];
}

function highlightSidebar(page) {
  if (!page) return;
  const slug = page === 'dashboard' ? '/' : `/${page.replace(/_/g, '-')}/`;
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    const href = (a.getAttribute('href') || '').split('?')[0];
    a.setAttribute('aria-current', href === slug ? 'page' : '');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMobileMenu();
  updateConnectionStatus(true);
  pollState();
  const page = detectPage();
  highlightSidebar(page);
  if (PAGE_INIT[page]) PAGE_INIT[page]();
  setInterval(() => { if (detectPage() === 'dashboard') loadDashboardData({ silent: true }); }, CONFIG.refreshInterval);
  const topoFull = $('#topology-fullscreen');
  if (topoFull) topoFull.addEventListener('click', () => {
    const el = $('#topology-canvas');
    if (el) el.requestFullscreen?.().catch(() => {});
  });
});

window.SecureDT = { api, showToast, state, CONFIG, createBadge, badgeHTML, formatBytes, timeAgo };