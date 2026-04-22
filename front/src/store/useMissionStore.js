import { create } from 'zustand';

export const useMissionStore = create((set) => ({
    missionId: null,
    missionType: 'photo',
    hint: null, // legacy — 단일 힌트 (하위 호환)
    // 미션 카드별 미리보기 힌트: { hint: string, vqa_hints: string[] }
    previewHints: { location: null, atmosphere: null },
    // 현재 진행 중인 미션 힌트: { hint: string, vqa_hints: string[] }
    activeHint: null,
    submissionResult: null,
    coupon: null,

    // Actions
    setMissionParams: (id, type) => set({ missionId: id, missionType: type }),
    setHint: (hint) => set({ hint }),
    setPreviewHint: (missionType, hintData) => set((state) => ({
        previewHints: { ...state.previewHints, [missionType]: hintData }
    })),
    setActiveHint: (hintData) => set({ activeHint: hintData }),
    setSubmissionResult: (result) => set({ submissionResult: result }),
    setCoupon: (coupon) => set({ coupon }),
    resetMission: () => set({ missionId: null, submissionResult: null, hint: null, activeHint: null }),
    resetAll: () => set({
        missionId: null,
        hint: null,
        activeHint: null,
        previewHints: { location: null, atmosphere: null },
        submissionResult: null,
        coupon: null,
    }),
}));
