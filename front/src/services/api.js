const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

async function request(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            throw new ApiError(data.error || data.message || 'API request failed', response.status);
        }

        return data;
    } catch (error) {
        if (error instanceof ApiError) throw error;
        throw new Error('Network error or server is down');
    }
}

export const api = {
    /**
     * @param {string} missionType 'location' | 'atmosphere'
     * @returns {Promise<{hint: string}>}
     */
    getTodayHint: async (missionType) => {
        return request(`/get-today-hint?mission_type=${missionType}`);
    },

    /**
     * @param {object} payload 
     * @param {string} payload.mission_type
     * @param {string} payload.user_id
     * @returns {Promise<{mission_id: string, message: string}>}
     */
    startMission: async (payload) => {
        return request('/api/mission/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
    },

    /**
     * @param {FormData} formData Must contain 'image', 'mission_id', and optionally 'model_selection'
     * @returns {Promise<{success: boolean, score: number, message: string, couponEligible: boolean, error?: string}>}
     */
    submitMission: async (formData) => {
        return request('/api/mission/submit', {
            method: 'POST',
            body: formData, // Browser sets Content-Type to multipart/form-data automatically
        });
    },

    /**
     * @param {string} missionId
     * @returns {Promise<{code: string, expires_at: string, description: string}>}
     */
    issueCoupon: async (missionId) => {
        return request('/api/coupon/issue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mission_id: missionId }),
        });
    }
};
