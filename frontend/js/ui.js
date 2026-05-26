/* ── Shared UI utilities ─────────────────────────────────────────────────── */

function toast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .4s'; setTimeout(() => el.remove(), 400); }, duration);
}

function formatTime(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(isoString) {
  if (!isoString) return '—';
  return `${formatDate(isoString)} ${formatTime(isoString)}`;
}

function tierBadge(tier) {
  const t = (tier || 'Bronze').toLowerCase();
  return `<span class="badge badge-${t}">${tier}</span>`;
}

function statusBadge(status) {
  const map = {
    Confirmed: 'info', CheckedIn: 'success', Boarded: 'success',
    Cancelled: 'error', Scheduled: 'info', Boarding: 'warn',
    Departed: 'info', Arrived: 'success',
  };
  const cls = map[status] || 'info';
  return `<span class="badge badge-${cls}">${status}</span>`;
}

function requireAuth() {
  if (!store.isLoggedIn()) {
    window.location.href = '/index.html';
    return false;
  }
  return true;
}

function updateNavUser() {
  const el = document.getElementById('nav-user');
  if (!el) return;
  if (store.isLoggedIn()) {
    el.innerHTML = `
      <span class="nav-badge">${tierBadge(store.tier)} ${store.ffn}</span>
      <button class="btn btn-ghost btn-sm" onclick="api.logout()">Sign out</button>
    `;
  } else {
    el.innerHTML = `<a href="/index.html" class="btn btn-primary btn-sm">Sign in</a>`;
  }
}

function renderScanUI(containerId, title, subtitle, buttonLabel, eventType, location) {
  const container = document.getElementById(containerId);
  container.innerHTML = `
    <div class="scan-wrapper">
      <div class="camera-box" id="cam-box">
        <video id="scan-video" autoplay muted playsinline></video>
        <canvas id="scan-canvas"></canvas>
        <div class="scan-ring" id="scan-ring"></div>
      </div>
      <div class="scan-status">
        <div class="status-icon" id="scan-icon">📷</div>
        <div class="status-text" id="scan-text">Initialising camera…</div>
      </div>
      <button class="btn btn-primary btn-lg" id="scan-btn" disabled>
        <div class="spinner hidden" id="scan-spinner"></div>
        <span id="scan-btn-label">${buttonLabel}</span>
      </button>
      <p class="text-muted" style="font-size:.8rem;max-width:280px;text-align:center;">
        ${subtitle}
      </p>
    </div>
  `;
}

// Confidence ring SVG
function confidenceRingHtml(confidence, size = 64) {
  const r = (size / 2) - 6;
  const circ = 2 * Math.PI * r;
  const dash = confidence * circ;
  const color = confidence > 0.75 ? 'var(--green)' : confidence > 0.5 ? 'var(--amber)' : 'var(--red)';
  const pct = Math.round(confidence * 100);
  return `
    <div class="confidence-ring">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="var(--border)" stroke-width="5"/>
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="${color}" stroke-width="5"
          stroke-dasharray="${dash} ${circ}" stroke-linecap="round"/>
      </svg>
      <div class="ring-value" style="color:${color}">${pct}%</div>
    </div>
  `;
}
