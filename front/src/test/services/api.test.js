import { api } from '../../services/api';

// fetch mock: AbortSignal을 직접 감지해 reject
const hangingFetch = (_url, options) =>
  new Promise((_res, rej) => {
    options?.signal?.addEventListener('abort', () => {
      rej(new DOMException('The operation was aborted.', 'AbortError'));
    });
  });

describe('api — fetch timeout (BUG 2)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it.each([
    ['getTodayHint', () => api.getTodayHint('location')],
    ['startMission', () => api.startMission({ mission_type: 'location', user_id: 'guest' })],
    ['submitMission', () => api.submitMission(new FormData())],
    ['issueCoupon', () => api.issueCoupon('mission-xyz')],
  ])('%s이 10초 내 응답 없으면 reject한다', async (_name, call) => {
    vi.spyOn(global, 'fetch').mockImplementation(hangingFetch);

    const promise = call();
    // .catch()로 rejection을 미리 등록해 "unhandled rejection" 경고 방지
    promise.catch(() => {});
    await vi.advanceTimersByTimeAsync(11000);

    await expect(promise).rejects.toThrow();
  });
});

describe('api auth headers', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('adds bearer token to user-owned mission calls', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ok: true }),
    });

    await api.getTodayHint('location', 'user-123', 'token-123');
    await api.startMission({ mission_type: 'location' }, 'token-123');
    await api.issueCoupon('mission-1', 'user-123', 'token-123');

    expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer token-123');
    expect(fetch.mock.calls[1][1].headers.Authorization).toBe('Bearer token-123');
    expect(fetch.mock.calls[2][1].headers.Authorization).toBe('Bearer token-123');
  });
});
