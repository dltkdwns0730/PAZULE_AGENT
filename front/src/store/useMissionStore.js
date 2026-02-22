import { create } from 'zustand';

export const useMissionStore = create((set) => ({
    missionId: null,
    missionType: 'photo', // default
    hint: null,
    submissionResult: null, // Holds the result from AI analysis (success, score, message, etc.)
    coupon: null, // Holds the issued coupon details

    // Actions
    setMissionParams: (id, type) => set({ missionId: id, missionType: type }),
    setHint: (hint) => set({ hint }),
    setSubmissionResult: (result) => set({ submissionResult: result }),
    setCoupon: (coupon) => set({ coupon }),
    resetMission: () => set({ missionId: null, submissionResult: null, hint: null }),
    resetAll: () => set({ missionId: null, hint: null, submissionResult: null, coupon: null })
}));
