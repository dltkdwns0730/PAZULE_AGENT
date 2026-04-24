import { renderHook, act } from '@testing-library/react';
import { useMission } from '../../hooks/useMission';
import { api } from '../../services/api';
import { useMissionStore } from '../../store/useMissionStore';

vi.mock('../../services/api', () => ({
  api: {
    getTodayHint: vi.fn(),
    startMission: vi.fn(),
    submitMission: vi.fn(),
    issueCoupon: vi.fn(),
  },
}));

vi.mock('../../store/useMissionStore', () => ({
  useMissionStore: vi.fn(),
}));

describe('useMission', () => {
  let store;

  beforeEach(() => {
    store = {
      missionId: 'test-id',
      previewHints: { location: null, atmosphere: null },
      setHint: vi.fn(),
      setPreviewHint: vi.fn(),
      setActiveHint: vi.fn(),
      setMissionParams: vi.fn(),
      setSubmissionResult: vi.fn(),
      setCoupon: vi.fn(),
    };
    useMissionStore.mockReturnValue(store);
  });

  it('sets isLoading while fetchHint is in flight', async () => {
    let resolve;
    api.getTodayHint.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      })
    );

    const { result } = renderHook(() => useMission());

    expect(result.current.isLoading).toBe(false);

    act(() => {
      result.current.fetchHint('location');
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolve({ hint: 'Find the bookshelf' });
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('resets isLoading after fetchHint errors', async () => {
    api.getTodayHint.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useMission());

    await act(async () => {
      await result.current.fetchHint('location');
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('stores an automatically issued coupon from a successful submission', async () => {
    const coupon = { code: 'AUTO1234', status: 'issued' };
    const submissionResult = {
      success: true,
      mission_id: 'test-id',
      coupon,
    };
    api.submitMission.mockResolvedValue(submissionResult);

    const { result } = renderHook(() => useMission());

    await act(async () => {
      await result.current.submitPhoto(new File(['image'], 'mission.jpg'));
    });

    expect(store.setSubmissionResult).toHaveBeenCalledWith(submissionResult);
    expect(store.setCoupon).toHaveBeenCalledWith(coupon);
  });
});
