import { useState } from 'react';
import { api } from '../services/api';
import { useMissionStore } from '../store/useMissionStore';

export function useMission() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const store = useMissionStore();

    const fetchHint = async (missionType) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getTodayHint(missionType);
            store.setPreviewHint(missionType, data.hint);
            return data.hint;
        } catch (err) {
            console.error('Failed to fetch hint:', err);
            store.setPreviewHint(missionType, null);
            return null;
        } finally {
            setIsLoading(false);
        }
    };

    const startMission = async (missionType, userId = 'guest') => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.startMission({ mission_type: missionType, user_id: userId });
            store.setMissionParams(data.mission_id, missionType);
            // API 응답 hint 또는 미리 로드된 previewHint를 activeHint로 저장
            const activeHint = data.hint ?? store.previewHints[missionType] ?? null;
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
            const result = await api.submitMission(formData);
            store.setSubmissionResult(result);
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
            const result = await api.issueCoupon(store.missionId);
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
