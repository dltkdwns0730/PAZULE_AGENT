const API_BASE = import.meta.env.PROD ? (import.meta.env.VITE_API_URL || '') : '';
const FETCH_TIMEOUT_MS = 10_000;

class AdminApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'AdminApiError';
    this.status = status;
  }
}

function authHeaders(accessToken) {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

async function request(path, accessToken, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...authHeaders(accessToken),
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new AdminApiError(
        payload.detail || payload.error || '관리자 API 요청에 실패했습니다.',
        response.status,
      );
    }
    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

function withQuery(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value);
  });
  return `${url.pathname}${url.search}`;
}

export const adminApi = {
  getOrganizations(accessToken) {
    return request('/api/admin/organizations', accessToken);
  },
  getSummary(accessToken, params = {}) {
    return request(withQuery('/api/admin/summary', params), accessToken);
  },
  getMissionSessions(accessToken, params = {}) {
    return request(withQuery('/api/admin/mission-sessions', params), accessToken);
  },
  getMissionSession(accessToken, missionId) {
    return request(`/api/admin/mission-sessions/${encodeURIComponent(missionId)}`, accessToken);
  },
  getCoupons(accessToken, params = {}) {
    return request(withQuery('/api/admin/coupons', params), accessToken);
  },
  redeemCoupon(accessToken, code) {
    return request(`/api/admin/coupons/${encodeURIComponent(code)}/redeem`, accessToken, {
      method: 'POST',
      body: JSON.stringify({ partner_pos_id: 'ADMIN-CONSOLE' }),
    });
  },
  getUsers(accessToken, params = {}) {
    return request(withQuery('/api/admin/users', params), accessToken);
  },
};
