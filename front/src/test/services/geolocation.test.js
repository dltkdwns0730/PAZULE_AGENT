import {
  getCurrentPosition,
  shouldSkipBrowserGps,
} from '../../services/geolocation';

describe('geolocation service', () => {
  it('skips browser geolocation when demo GPS validation is disabled', async () => {
    const originalGeolocation = navigator.geolocation;
    const getCurrentPositionMock = vi.fn();

    vi.stubEnv('VITE_SKIP_GPS_VALIDATION', 'true');

    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: { getCurrentPosition: getCurrentPositionMock },
    });

    await expect(getCurrentPosition()).resolves.toEqual({
      client_lat: 37.711988,
      client_lng: 126.6867095,
      accuracy_meters: 0,
    });

    expect(shouldSkipBrowserGps()).toBe(true);
    expect(getCurrentPositionMock).not.toHaveBeenCalled();

    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: originalGeolocation,
    });
    vi.unstubAllEnvs();
  });
});
