import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

export default function Map() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('outdoor'); // 'outdoor' or 'indoor'

    return (
        <div className="font-display h-full w-full bg-white flex flex-col relative overflow-hidden">
            
            {/* Header */}
            <header className="pt-10 px-6 flex items-center justify-between flex-shrink-0 bg-white z-20">
                <button onClick={() => navigate(-1)} className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey text-dark-teal">
                    <span className="material-symbols-outlined">arrow_back_ios_new</span>
                </button>
                <h1 className="text-dark-teal text-xl font-bold">지혜의 지도</h1>
                <div className="w-10 h-10"></div>
            </header>

            {/* Tab Navigation */}
            <div className="px-6 py-4 flex-shrink-0">
                <div className="flex bg-light-grey/50 p-1 rounded-2xl">
                    <button 
                        onClick={() => setActiveTab('outdoor')}
                        className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'outdoor' ? 'bg-white text-dark-teal shadow-sm' : 'text-gray-400'}`}
                    >
                        야외 지도
                    </button>
                    <button 
                        onClick={() => setActiveTab('indoor')}
                        className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'indoor' ? 'bg-white text-dark-teal shadow-sm' : 'text-gray-400'}`}
                    >
                        실내 도면
                    </button>
                </div>
            </div>

            {/* Map Content */}
            <main className="flex-1 relative overflow-hidden bg-gray-50">
                {activeTab === 'outdoor' ? (
                    <div className="w-full h-full">
                        {/* Using Google Maps Embed as a default robust outdoor map */}
                        <iframe 
                            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m12!1m3!1d12613.59368537549!2d126.6749174627191!3d37.71158529555437!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c91796be4b0d5%3A0xc3f8485202860df8!2z7YyM7KO87Lac7YyQ64uo7KeA!5e0!3m2!1sko!2skr!4v1713859000000!5m2!1sko!2skr"
                            width="100%" 
                            height="100%" 
                            style={{ border: 0 }} 
                            allowFullScreen="" 
                            loading="lazy" 
                            referrerPolicy="no-referrer-when-downgrade"
                            title="Paju Book City Map"
                        ></iframe>
                        
                        <div className="absolute bottom-6 right-6 bg-white/90 backdrop-blur-md px-4 py-3 rounded-2xl shadow-xl border border-dark-teal/5 z-30">
                            <p className="text-dark-teal font-bold text-xs">파주 출판도시</p>
                            <p className="text-gray-400 text-[10px]">탐험 지역 전체 보기</p>
                        </div>
                    </div>
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center p-4">
                        <div className="w-full h-full rounded-3xl overflow-hidden bg-white shadow-inner relative">
                            <TransformWrapper
                                initialScale={1}
                                initialPositionX={0}
                                initialPositionY={0}
                            >
                                <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }} contentStyle={{ width: "100%", height: "100%" }}>
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
                                지혜의 숲 1관 실내도
                            </div>
                            
                            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-md border border-gray-100 flex items-center gap-2 z-30">
                                <span className="material-symbols-outlined text-sm text-dark-teal">zoom_in</span>
                                <span className="text-[10px] text-gray-500 font-medium">핀치하여 확대/축소 가능</span>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* Spacer for bottom nav */}
            <div className="h-4 flex-shrink-0"></div>
        </div>
    );
}
