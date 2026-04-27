import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const NAVER_MAP_CLIENT_ID = import.meta.env.VITE_NAVER_MAP_CLIENT_ID;
const SITE_CENTER = {
    lat: Number(import.meta.env.VITE_MISSION_SITE_LAT || 37.711988),
    lng: Number(import.meta.env.VITE_MISSION_SITE_LON || 126.6867095),
};
const SITE_RADIUS_METERS = Number(import.meta.env.VITE_MISSION_SITE_RADIUS_METERS || 300);

function loadNaverMapScript() {
    if (window.naver?.maps) {
        return Promise.resolve();
    }

    if (!NAVER_MAP_CLIENT_ID) {
        return Promise.reject(new Error('missing_naver_map_client_id'));
    }

    const existing = document.querySelector('script[data-naver-map-sdk="true"]');
    if (existing) {
        return new Promise((resolve, reject) => {
            existing.addEventListener('load', resolve, { once: true });
            existing.addEventListener('error', reject, { once: true });
        });
    }

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.dataset.naverMapSdk = 'true';
        script.src = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpClientId=${NAVER_MAP_CLIENT_ID}`;
        script.async = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function OutdoorMap() {
    const mapRef = useRef(null);
    const [status, setStatus] = useState('loading');

    useEffect(() => {
        let disposed = false;

        loadNaverMapScript()
            .then(() => {
                if (disposed || !mapRef.current) return;

                const center = new window.naver.maps.LatLng(SITE_CENTER.lat, SITE_CENTER.lng);
                const map = new window.naver.maps.Map(mapRef.current, {
                    center,
                    zoom: 16,
                    minZoom: 14,
                    scaleControl: false,
                    logoControl: true,
                    mapDataControl: false,
                    zoomControl: true,
                    zoomControlOptions: {
                        position: window.naver.maps.Position.TOP_RIGHT,
                    },
                });

                new window.naver.maps.Marker({
                    position: center,
                    map,
                    title: 'PAZULE 미션 구역',
                });

                new window.naver.maps.Circle({
                    map,
                    center,
                    radius: SITE_RADIUS_METERS,
                    strokeColor: '#37776f',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#4ce0b3',
                    fillOpacity: 0.18,
                });

                setStatus('ready');
            })
            .catch(() => {
                if (!disposed) setStatus('error');
            });

        return () => {
            disposed = true;
        };
    }, []);

    return (
        <div className="w-full h-full relative">
            <div ref={mapRef} className="w-full h-full" />
            {status !== 'ready' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white text-center px-8">
                    <span className="material-symbols-outlined text-4xl text-dark-teal mb-3">map</span>
                    <p className="text-dark-teal font-bold">
                        {status === 'loading' ? '지도를 불러오는 중입니다' : 'Naver Maps API 키를 확인해주세요'}
                    </p>
                    <p className="text-gray-400 text-xs mt-2">
                        미션 구역 중심: {SITE_CENTER.lat.toFixed(5)}, {SITE_CENTER.lng.toFixed(5)}
                    </p>
                </div>
            )}
            <div className="absolute bottom-6 right-6 bg-white/90 backdrop-blur-md px-4 py-3 rounded-2xl shadow-xl border border-dark-teal/5 z-30">
                <p className="text-dark-teal font-bold text-xs">PAZULE 미션 구역</p>
                <p className="text-gray-400 text-[10px]">반경 {SITE_RADIUS_METERS}m 안에서 미션을 진행하세요</p>
            </div>
        </div>
    );
}

export default function Map() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('outdoor');

    return (
        <div className="font-display h-full w-full bg-white flex flex-col relative overflow-hidden">
            <header className="pt-10 px-6 flex items-center justify-between flex-shrink-0 bg-white z-20">
                <button onClick={() => navigate(-1)} className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey text-dark-teal">
                    <span className="material-symbols-outlined">arrow_back_ios_new</span>
                </button>
                <h1 className="text-dark-teal text-xl font-bold">미션 지도</h1>
                <div className="w-10 h-10" />
            </header>

            <div className="px-6 py-4 flex-shrink-0">
                <div className="flex bg-light-grey/50 p-1 rounded-2xl">
                    <button
                        onClick={() => setActiveTab('outdoor')}
                        className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'outdoor' ? 'bg-white text-dark-teal shadow-sm' : 'text-gray-400'}`}
                    >
                        실외 지도
                    </button>
                    <button
                        onClick={() => setActiveTab('indoor')}
                        className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'indoor' ? 'bg-white text-dark-teal shadow-sm' : 'text-gray-400'}`}
                    >
                        실내 안내
                    </button>
                </div>
            </div>

            <main className="flex-1 relative overflow-hidden bg-gray-50">
                {activeTab === 'outdoor' ? (
                    <OutdoorMap />
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center p-4">
                        <div className="w-full h-full rounded-3xl overflow-hidden bg-white shadow-inner relative">
                            <TransformWrapper initialScale={1} initialPositionX={0} initialPositionY={0}>
                                <TransformComponent wrapperStyle={{ width: '100%', height: '100%' }} contentStyle={{ width: '100%', height: '100%' }}>
                                    <div className="w-full h-full flex items-center justify-center bg-warm-cream/30">
                                        <img
                                            src="https://images.unsplash.com/photo-1517094857443-80776527e05e?q=80&w=2000"
                                            alt="Indoor Floor Plan"
                                            className="max-w-none w-[150%] object-contain"
                                        />
                                    </div>
                                </TransformComponent>
                            </TransformWrapper>

                            <div className="absolute top-6 left-6 bg-dark-teal/90 text-white px-3 py-1.5 rounded-full text-[10px] font-bold shadow-lg z-30">
                                실내 안내도
                            </div>
                        </div>
                    </div>
                )}
            </main>

            <div className="h-4 flex-shrink-0" />
        </div>
    );
}
