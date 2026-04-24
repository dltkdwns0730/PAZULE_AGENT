import { renderHook, act } from '@testing-library/react';
import { useMission } from '../../hooks/useMission';
import { api } from '../../services/api';
import { getCurrentPosition } from '../../services/geolocation';
import { useMissionStore } from '../../store/useMissionStore';

vi.mock('../../services/api', () => ({
  api: {
    getTodayHint: vi.fn(),
    startMission: vi.fn(),
    submitMission: vi.fn(),
    issueCoupon: vi.fn(),
  },
}));

vi.mock('../../services/geolocation', () => ({
  getCurrentPosition: vi.fn(),
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
    getCurrentPosition.mockResolvedValue({
      client_lat: 37.711988,
      client_lng: 126.6867095,
      accuracy_meters: 20,
    });
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
    expect(api.submitMission).toHaveBeenCalledTimes(1);

    const formData = api.submitMission.mock.calls[0][0];
    expect(formData.get('client_lat')).toBe('37.711988');
    expect(formData.get('client_lng')).toBe('126.6867095');
    expect(formData.get('accuracy_meters')).toBe('20');
  });

  it('includes current GPS when starting a mission', async () => {
    api.startMission.mockResolvedValue({
      mission_id: 'mission-1',
      hint: 'hint',
      vqa_hints: [],
    });

    const { result } = renderHook(() => useMission());

    await act(async () => {
      await result.current.startMission('location', 'guest');
    });

    expect(api.startMission).toHaveBeenCalledWith({
      mission_type: 'location',
      user_id: 'guest',
      client_lat: 37.711988,
      client_lng: 126.6867095,
      accuracy_meters: 20,
    });
  });
});
