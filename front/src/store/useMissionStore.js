import { create } from 'zustand';

export const useMissionStore = create((set) => ({
    missionId: null,
    missionType: 'photo', // default
    hint: null, // legacy — 단일 힌트 (하위 호환)
    previewHints: { location: null, atmosphere: null }, // 미션 카드별 미리보기 힌트
    activeHint: null, // 현재 진행 중인 미션의 힌트
    submissionResult: null, // Holds the result from AI analysis (success, score, message, etc.)
    coupon: null, // Holds the issued coupon details

    // Actions
    setMissionParams: (id, type) => set({ missionId: id, missionType: type }),
    setHint: (hint) => set({ hint }),
    setPreviewHint: (missionType, hint) => set((state) => ({
        previewHints: { ...state.previewHints, [missionType]: hint }
    })),
    setActiveHint: (hint) => set({ activeHint: hint }),
    setSubmissionResult: (result) => set({ submissionResult: result }),
    setCoupon: (coupon) => set({ coupon }),
    resetMission: () => set({ missionId: null, submissionResult: null, hint: null, activeHint: null }),
    resetAll: () => set({ missionId: null, hint: null, activeHint: null, previewHints: { location: null, atmosphere: null }, submissionResult: null, coupon: null })
}));
