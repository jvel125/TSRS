/* ── TSRS API client ─────────────────────────────────────────────────────── */
const API_BASE = 'http://127.0.0.1:8000/api/v1';

const store = {
  get token()      { return localStorage.getItem('tsrs_token'); },
  set token(v)     { v ? localStorage.setItem('tsrs_token', v) : localStorage.removeItem('tsrs_token'); },
  get passengerId(){ return localStorage.getItem('tsrs_pid'); },
  set passengerId(v){ v ? localStorage.setItem('tsrs_pid', v) : localStorage.removeItem('tsrs_pid'); },
  get ffn()        { return localStorage.getItem('tsrs_ffn'); },
  set ffn(v)       { v ? localStorage.setItem('tsrs_ffn', v) : localStorage.removeItem('tsrs_ffn'); },
  get tier()       { return localStorage.getItem('tsrs_tier'); },
  set tier(v)      { v ? localStorage.setItem('tsrs_tier', v) : localStorage.removeItem('tsrs_tier'); },
  clear() {
    ['tsrs_token','tsrs_pid','tsrs_ffn','tsrs_tier'].forEach(k => localStorage.removeItem(k));
  },
  isLoggedIn() { return !!this.token; },
};

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (store.token) headers['Authorization'] = `Bearer ${store.token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.detail || data.message || `HTTP ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

const api = {
  // Auth
  register: (body) => apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login:    (body) => apiFetch('/auth/login',    { method: 'POST', body: JSON.stringify(body) }),

  // Passengers
  getMe:    ()     => apiFetch('/passengers/me'),

  // Flights
  listFlights: ()     => apiFetch('/flights'),
  getFlight:   (id)   => apiFetch(`/flights/${id}`),
  myBookings:  ()     => apiFetch('/flights/me/bookings'),

  // Biometrics
  enrollFace:  (descriptor) => apiFetch('/biometrics/enroll', {
    method: 'POST', body: JSON.stringify({ descriptor }),
  }),
  verifyFace:  (descriptor) => apiFetch('/biometrics/verify', {
    method: 'POST', body: JSON.stringify({ descriptor }),
  }),
  revokeFace:  () => apiFetch('/biometrics/enroll', { method: 'DELETE' }),

  // Access control
  gateAccess: (descriptor, location, event_type) => apiFetch('/access/gate', {
    method: 'POST',
    body: JSON.stringify({ descriptor, location, event_type }),
  }),
  myLogs: (limit = 20) => apiFetch(`/access/logs?limit=${limit}`),
  adminLogs: (limit = 100) => apiFetch(`/access/admin/logs?limit=${limit}`),

  // Helpers
  saveSession(token) {
    store.token = token.access_token;
    store.passengerId = token.passenger_id;
    store.ffn = token.frequent_flyer_number;
    store.tier = token.tier;
  },
  logout() { store.clear(); window.location.href = '/index.html'; },
};
