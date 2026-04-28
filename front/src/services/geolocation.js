export class GeolocationError extends Error {
  constructor(message, code = 'gps_unavailable') {
    super(message);
    this.name = 'GeolocationError';
    this.code = code;
  }
}

export function shouldSkipBrowserGps() {
  return import.meta.env.VITE_SKIP_GPS_VALIDATION === 'true';
}

export function getDemoMissionLocation() {
  return {
    client_lat: Number(import.meta.env.VITE_MISSION_SITE_LAT || 37.711988),
    client_lng: Number(import.meta.env.VITE_MISSION_SITE_LON || 126.6867095),
    accuracy_meters: 0,
  };
}

export function getCurrentPosition(options = {}) {
  if (shouldSkipBrowserGps()) {
    return Promise.resolve(getDemoMissionLocation());
  }

  if (!navigator.geolocation) {
    return Promise.reject(
      new GeolocationError('GPS를 지원하지 않는 브라우저입니다.', 'gps_unsupported')
    );
  }

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          client_lat: position.coords.latitude,
          client_lng: position.coords.longitude,
          accuracy_meters: position.coords.accuracy,
        });
      },
      (error) => {
        reject(
          new GeolocationError(
            '위치 권한을 허용한 뒤 현장 근처에서 다시 시도해주세요.',
            error.code === error.PERMISSION_DENIED ? 'gps_permission_denied' : 'gps_unavailable'
          )
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 10_000,
        maximumAge: 30_000,
        ...options,
      }
    );
  });
}
