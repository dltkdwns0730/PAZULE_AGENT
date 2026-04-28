import { useState } from 'react';
import { api } from '../services/api';
import { getCurrentPosition } from '../services/geolocation';
import { useAuthStore } from '../store/useAuthStore';
import { useMissionStore } from '../store/useMissionStore';

export function useMission() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const store = useMissionStore();
    const { userId, accessToken, isAuthenticated } = useAuthStore();

    const requireAuth = () => {
        if (!isAuthenticated || !userId || !accessToken) {
            throw new Error('Login is required to start missions.');
        }
        return { userId, accessToken };
    };

    const fetchHint = async (missionType, requestedUserId = userId) => {
        setIsLoading(true);
        setError(null);
        try {
            const auth = requireAuth();
            const data = await api.getTodayHint(
                missionType,
                requestedUserId || auth.userId,
                auth.accessToken,
            );
            const hintData = { 
                hint: data.hint, 
                vqa_hints: data.vqa_hints ?? [],
                completed: data.completed ?? false 
            };
            store.setPreviewHint(missionType, hintData);
            return hintData;
        } catch (err) {
            console.error('Failed to fetch hint:', err);
            store.setPreviewHint(missionType, null);
            return null;
        } finally {
            setIsLoading(false);
        }
    };

    const startMission = async (missionType, requestedUserId = userId) => {
        setIsLoading(true);
        setError(null);
        try {
            const auth = requireAuth();
            const location = await getCurrentPosition();
            const data = await api.startMission({
                mission_type: missionType,
                user_id: requestedUserId || auth.userId,
                ...location,
            }, auth.accessToken);
            store.setMissionParams(data.mission_id, missionType);
            // API 응답 또는 미리 로드된 previewHint를 activeHint로 저장 ({ hint, vqa_hints })
            const activeHint = (data.hint != null)
                ? { hint: data.hint, vqa_hints: data.vqa_hints ?? [] }
                : store.previewHints[missionType] ?? null;
            store.setActiveHint(activeHint);
            return data.mission_id;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const submitPhoto = async (file) => {
        if (!store.missionId) {
            throw new Error('Mission not started');
        }

        setIsLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('image', file);
        formData.append('mission_id', store.missionId);

        try {
            const location = await getCurrentPosition();
            if (location.client_lat != null) {
                formData.append('client_lat', location.client_lat);
            }
            if (location.client_lng != null) {
                formData.append('client_lng', location.client_lng);
            }
            if (location.accuracy_meters != null) {
                formData.append('accuracy_meters', location.accuracy_meters);
            }
            const auth = requireAuth();
            const result = await api.submitMission(formData, auth.accessToken);
            store.setSubmissionResult(result);
            if (result.coupon) {
                store.setCoupon(result.coupon);
            }
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const issueCoupon = async () => {
        if (!store.missionId) {
            throw new Error('No active mission found to issue coupon');
        }

        setIsLoading(true);
        setError(null);
        try {
            const auth = requireAuth();
            const result = await api.issueCoupon(
                store.missionId,
                auth.userId,
                auth.accessToken,
            );
            // Explicitly set coupon in store
            store.setCoupon(result);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    return {
        isLoading,
        error,
        fetchHint,
        startMission,
        submitPhoto,
        issueCoupon
    };
}
