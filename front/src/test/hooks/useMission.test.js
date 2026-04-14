import { renderHook, act } from '@testing-library/react';
import { useMission } from '../../hooks/useMission';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getTodayHint: vi.fn(),
    startMission: vi.fn(),
    submitMission: vi.fn(),
    issueCoupon: vi.fn(),
  },
}));

vi.mock('../../store/useMissionStore', () => ({
  useMissionStore: vi.fn(() => ({
    missionId: 'test-id',
    setHint: vi.fn(),
    setMissionParams: vi.fn(),
    setSubmissionResult: vi.fn(),
    setCoupon: vi.fn(),
  })),
}));

describe('useMission — fetchHint isLoading 관리 (BUG 3)', () => {
  it('fetchHint 호출 중 isLoading이 true다', async () => {
    let resolve;
    api.getTodayHint.mockReturnValue(
      new Promise((r) => { resolve = r; })
    );

    const { result } = renderHook(() => useMission());

    expect(result.current.isLoading).toBe(false);

    act(() => {
      result.current.fetchHint('location');
    });

    // fetchHint가 isLoading을 관리하지 않으면 여기서 FAIL
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolve({ hint: 'Find the bookshelf' });
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('fetchHint 에러 후에도 isLoading이 false다', async () => {
    api.getTodayHint.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useMission());

    await act(async () => {
      await result.current.fetchHint('location');
    });

    expect(result.current.isLoading).toBe(false);
  });
});
