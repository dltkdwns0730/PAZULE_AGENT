/**
 * API Service for interacting with the backend endpoints.
 */

const API_BASE = import.meta.env.PROD ? (import.meta.env.VITE_API_URL || '') : '';

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
        this.name = 'ApiError';
    }
}

const FETCH_TIMEOUT_MS = 10_000;

function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    return fetch(url, { ...options, signal: controller.signal }).finally(() => {
        clearTimeout(timeoutId);
    });
}

async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(errorData.detail || errorData.error || 'API Request Failed', response.status);
    }
    return response.json();
}

export const api = {
    /**
     * Get the daily hint for a mission type
     * @param {string} missionType 'location' or 'atmosphere'
     */
    async getTodayHint(missionType = 'location') {
        const response = await fetchWithTimeout(`${API_BASE}/get-today-hint?mission_type=${missionType}`);
        return handleResponse(response);
    },

    /**
     * Start a new mission session
     * @param {Object} data - { user_id: string, mission_type: string }
     */
    async startMission(data) {
        const response = await fetchWithTimeout(`${API_BASE}/api/mission/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        return handleResponse(response);
    },

    /**
     * Submit a photo for verification
     * @param {FormData} formData - Contains 'image' (File) and 'mission_id' (string)
     */
    async submitMission(formData) {
        const response = await fetchWithTimeout(`${API_BASE}/api/mission/submit`, {
            method: 'POST',
            // Do not set Content-Type header when sending FormData;
            // the browser sets it automatically with the boundary
            body: formData,
        });

        // The submission endpoint might return 200 with success: false for wrong photos.
        // handleResponse will throw on 4xx/5xx.
        return handleResponse(response);
    },

    /**
     * Issue a coupon after a successful mission
     * @param {string} missionId - The ID of the successful mission
     */
    async issueCoupon(missionId) {
        const response = await fetchWithTimeout(`${API_BASE}/api/coupon/issue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mission_id: missionId }),
        });
        return handleResponse(response);
    },
};
