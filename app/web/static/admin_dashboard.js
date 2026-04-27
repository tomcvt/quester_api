/* =============================================================
   admin_dashboard.js — Quester admin dashboard logic
   ============================================================= */

'use strict';

// ── Column definitions ────────────────────────────────────────

const USER_COLUMNS = [
  { key: 'id',              label: 'ID' },
  { key: 'username',        label: 'Username' },
  { key: 'phone_number',    label: 'Phone' },
  { key: 'role',            label: 'Role' },
  { key: 'public_id',       label: 'Public ID' },
  { key: 'installation_id', label: 'Installation ID' },
];

const QUEST_COLUMNS = [
  { key: 'id',           label: 'ID' },
  { key: 'name',         label: 'Name' },
  // { key: 'type',         label: 'Type' },
  { key: 'reward_type',  label: 'Reward Type' },
  { key: 'reward_value', label: 'Reward Value' },
  { key: 'status',       label: 'Status' },
  { key: 'group_id',     label: 'Group ID' },
  { key: 'creator_id',   label: 'Creator ID' },
  // { key: 'date',         label: 'Date' },
  // { key: 'deadline_end', label: 'Deadline' },
  { key: 'deadline',     label: 'Deadline' },
  { key: 'public_id',    label: 'Public ID' },
];

// ── App state ─────────────────────────────────────────────────

const state = {
  activeTab: 'users',
  users:  { page: 0, size: 20, total: 0, totalPages: 0 },
  quests: { page: 0, size: 20, total: 0, totalPages: 0, filters: {} },
};

const STUB_TABS = new Set(['groups', 'group-members']);

// ── Helpers ───────────────────────────────────────────────────

function redirectIfUnauthorized(status) {
  if (status === 401 || status === 403) {
    window.location.href = '/login';
    return true;
  }
  return false;
}

function formatCell(value, key) {
  if (value === null || value === undefined) return { text: '—', cls: 'null' };

  // UUID detection
  if (typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)) {
    return { text: value.slice(0, 8) + '…', cls: 'uuid', title: value };
  }

  // Datetime — strip milliseconds for readability
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    return { text: value.replace('T', ' ').slice(0, 19), cls: '' };
  }

  // Status
  if (key === 'status') return { text: String(value), cls: `status-${value}` };

  // Role
  if (key === 'role') return { text: String(value), cls: `role-${value}` };

  const text = String(value);
  return { text: text.length > 40 ? text.slice(0, 40) + '…' : text, cls: '', title: text };
}

// ── Rendering ─────────────────────────────────────────────────

function renderTable(containerId, items, columns) {
  const container = document.getElementById(containerId);

  if (!items || items.length === 0) {
    container.innerHTML = '<div class="state-message">No results found.</div>';
    return;
  }

  const headers = columns.map(c => `<th>${c.label}</th>`).join('');

  const rows = items.map(item => {
    const cells = columns.map(c => {
      const { text, cls, title } = formatCell(item[c.key], c.key);
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : (item[c.key] != null ? ` title="${escapeHtml(String(item[c.key]))}"` : '');
      return `<td class="${cls}"${titleAttr}>${escapeHtml(text)}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');

  container.innerHTML = `
    <div class="data-table-wrap">
      <table>
        <thead><tr>${headers}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderPagination(containerId, tabKey, page, totalPages, total, onPrev, onNext) {
  const container = document.getElementById(containerId);
  const size = state[tabKey].size;
  const from = total === 0 ? 0 : page * size + 1;
  const to   = Math.min((page + 1) * size, total);

  container.innerHTML = `
    <div class="pagination">
      <span class="page-info">Showing ${from}–${to} of ${total}</span>
      <div class="page-controls">
        <button class="btn btn-secondary" id="${containerId}-prev"${page === 0 ? ' disabled' : ''}>← Prev</button>
        <span class="page-info">Page ${page + 1} / ${Math.max(totalPages, 1)}</span>
        <button class="btn btn-secondary" id="${containerId}-next"${page >= totalPages - 1 ? ' disabled' : ''}>Next →</button>
      </div>
    </div>`;

  document.getElementById(`${containerId}-prev`).addEventListener('click', onPrev);
  document.getElementById(`${containerId}-next`).addEventListener('click', onNext);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Data fetching ─────────────────────────────────────────────

async function fetchUsers(page) {
  const params = new URLSearchParams({ page, size: state.users.size });
  const res = await fetch(`/api/v1/users/all?${params}`);
  if (redirectIfUnauthorized(res.status)) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

async function fetchQuests(page, filters = {}) {
  const params = new URLSearchParams({ page, size: state.quests.size });
  if (filters.name)       params.set('name',       filters.name);
  if (filters.status)     params.set('status',     filters.status);
  if (filters.group_id)   params.set('group_id',   filters.group_id);
  if (filters.creator_id) params.set('creator_id', filters.creator_id);
  const res = await fetch(`/api/v1/quests/all?${params}`);
  if (redirectIfUnauthorized(res.status)) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ── Tab loaders ───────────────────────────────────────────────

async function loadUsers() {
  const tableEl = document.getElementById('users-table');
  tableEl.innerHTML = '<div class="state-message">Loading…</div>';

  try {
    const data = await fetchUsers(state.users.page);
    if (!data) return;

    state.users.total      = data.total;
    state.users.totalPages = data.total_pages;

    renderTable('users-table', data.items, USER_COLUMNS);
    renderPagination(
      'users-pagination', 'users',
      state.users.page, data.total_pages, data.total,
      () => { state.users.page--; loadUsers(); },
      () => { state.users.page++; loadUsers(); },
    );
  } catch (e) {
    tableEl.innerHTML = `<div class="state-message error">${escapeHtml(e.message)}</div>`;
  }
}

async function loadQuests() {
  const tableEl = document.getElementById('quests-table');
  tableEl.innerHTML = '<div class="state-message">Loading…</div>';

  try {
    const data = await fetchQuests(state.quests.page, state.quests.filters);
    if (!data) return;

    state.quests.total      = data.total;
    state.quests.totalPages = data.total_pages;

    renderTable('quests-table', data.items, QUEST_COLUMNS);
    renderPagination(
      'quests-pagination', 'quests',
      state.quests.page, data.total_pages, data.total,
      () => { state.quests.page--; loadQuests(); },
      () => { state.quests.page++; loadQuests(); },
    );
  } catch (e) {
    tableEl.innerHTML = `<div class="state-message error">${escapeHtml(e.message)}</div>`;
  }
}

// ── Tab switching ─────────────────────────────────────────────

function switchTab(tabName) {
  if (STUB_TABS.has(tabName)) return;

  state.activeTab = tabName;

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.toggle('active', el.id === `tab-${tabName}`);
  });

  if (tabName === 'users')  { state.users.page  = 0; loadUsers();  }
  if (tabName === 'quests') { state.quests.page = 0; loadQuests(); }
}

// ── Quest filters ─────────────────────────────────────────────

function applyQuestFilters() {
  state.quests.page    = 0;
  state.quests.filters = {
    name:       document.getElementById('filter-quest-name').value.trim()       || undefined,
    status:     document.getElementById('filter-quest-status').value            || undefined,
    group_id:   document.getElementById('filter-quest-group-id').value          || undefined,
    creator_id: document.getElementById('filter-quest-creator-id').value        || undefined,
  };
  loadQuests();
}

function resetQuestFilters() {
  document.getElementById('filter-quest-name').value       = '';
  document.getElementById('filter-quest-status').value     = '';
  document.getElementById('filter-quest-group-id').value   = '';
  document.getElementById('filter-quest-creator-id').value = '';
  state.quests.filters = {};
  state.quests.page    = 0;
  loadQuests();
}

// ── Bootstrap ─────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Wire tabs — stubs are un-clickable
  document.querySelectorAll('.tab-btn:not(.stub)').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Wire quest filter controls
  document.getElementById('quest-apply-btn').addEventListener('click', applyQuestFilters);
  document.getElementById('quest-reset-btn').addEventListener('click', resetQuestFilters);

  // Allow Enter in any quest filter input to apply
  document.querySelectorAll('#tab-quests .filters input, #tab-quests .filters select').forEach(el => {
    el.addEventListener('keydown', e => { if (e.key === 'Enter') applyQuestFilters(); });
  });

  // Load default tab
  loadUsers();
});
