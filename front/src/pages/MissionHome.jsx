import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMission } from "../hooks/useMission";
import { useMissionStore } from "../store/useMissionStore";

export default function MissionHome() {
    const navigate = useNavigate();
    const { fetchHint, startMission, isLoading } = useMission();
    const { hint } = useMissionStore();

    const [isHintRevealed, setIsHintRevealed] = useState(false);

    useEffect(() => {
        fetchHint('location');
    }, []);

    const handleStartMission = async (type) => {
        if (isLoading) return;
        try {
            await startMission(type);
            navigate('/mission/submit');
        } catch (error) {
            alert(error.message || '미션 시작에 실패했습니다.');
        }
    };

    return (
        <div className="font-display h-full w-full flex items-center justify-center overflow-hidden relative bg-white">

            {/* Background Blur Elements */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-10">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-coral-start rounded-full blur-[100px] -translate-y-1/2 translate-x-1/4"></div>
                <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-dark-teal rounded-full blur-[100px] translate-y-1/2 -translate-x-1/4"></div>
            </div>

            <div className="relative w-full h-full flex flex-col z-10">

                {/* Header */}
                <header className="pt-10 px-6 flex justify-between items-center bg-white flex-shrink-0">
                    <div className="flex flex-col">
                        <span className="text-gray-400 text-sm font-medium">다시 오셨군요,</span>
                        <h1 className="text-dark-teal text-2xl font-bold tracking-tight">안녕하세요, 탐험가님</h1>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-light-grey flex items-center justify-center border border-gray-100 text-dark-teal shadow-sm">
                        <span className="material-symbols-outlined text-2xl">person</span>
                    </div>
                </header>

                {/* Main Content Scroll */}
                <main className="flex-1 px-6 py-6 overflow-y-auto no-scrollbar bg-white">

                    {/* Today's Hint (Moved to Top) */}
                    <div className="mb-8">
                        <h2 className="text-dark-teal font-bold text-lg mb-3">오늘의 힌트</h2>
                        <div
                            onClick={() => setIsHintRevealed(true)}
                            className={`bg-light-grey rounded-3xl p-5 relative overflow-hidden transition-colors border border-gray-100/50 ${isHintRevealed ? 'bg-white shadow-soft transition-all duration-300' : 'cursor-pointer hover:bg-gray-200 active:bg-gray-300'}`}
                        >
                            <div className="flex items-start gap-4">
                                <div className={`w-10 h-10 shrink-0 rounded-full flex items-center justify-center shadow-sm transition-colors ${isHintRevealed ? 'bg-coral-end text-white' : 'bg-white text-coral-end'}`}>
                                    <span className="material-symbols-outlined">tips_and_updates</span>
                                </div>
                                <div className="flex-1 mt-0.5">
                                    <p className="text-coral-end text-[10px] font-bold uppercase tracking-wider mb-1">
                                        {isHintRevealed ? '힌트 공개됨' : '탭하여 확인'}
                                    </p>
                                    
                                    {/* 항상 유지되는 기존 티저 힌트 */}
                                    <p className="text-gray-600 font-medium text-sm leading-relaxed">
                                        오래된 종이 향기와 새 커피 향이 만나는 곳...
                                    </p>
                                    
                                    {/* 숨겨진 실제 API 힌트 (클릭 시 하단에 펼쳐짐) */}
                                    {isHintRevealed && (
                                        <div className="mt-4 pt-3 border-t border-gray-100 flex items-start gap-2 animate-fade-in-up">
                                            <span className="material-symbols-outlined text-coral-end text-[18px]">key</span>
                                            <p className="text-dark-teal font-bold text-[13px] leading-snug">
                                                {hint || "오늘의 힌트를 불러오는 중..."}
                                            </p>
                                        </div>
                                    )}
                                </div>
                                {!isHintRevealed && (
                                    <span className="material-symbols-outlined text-gray-300 text-xl mt-2">chevron_right</span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Active Missions */}
                    <div className="space-y-4 pb-4">
                        <div className="flex justify-between items-end">
                            <h2 className="text-dark-teal font-bold text-lg">미션</h2>
                            <span className="text-coral-end text-xs font-semibold uppercase tracking-widest bg-pale-coral px-2.5 py-1 rounded-md">2개 진행 중</span>
                        </div>

                        {/* Mission Card 1 (Location Hunt - Connected to API) */}
                        <div
                            onClick={() => handleStartMission('location')}
                            className={`bg-warm-cream rounded-[2rem] p-6 shadow-card border border-pale-border transform transition-all duration-300 cursor-pointer hover:border-coral-end/30 hover:shadow-lg active:scale-[0.98] relative z-20 ${isLoading ? 'opacity-70 pointer-events-none' : ''}`}
                        >
                            {isLoading && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm rounded-[2rem] z-10 flex items-center justify-center">
                                    <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">location_on</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">탐험</span>
                            </div>
                            <h3 className="text-dark-teal text-xl font-bold mb-1">장소 찾기</h3>
                            <p className="text-gray-400 text-sm leading-snug">지혜의 숲 깊은 곳에 숨겨진 비밀 안뜰을 찾아보세요.</p>
                        </div>

                        {/* Mission Card 2 (Atmosphere) */}
                        <div
                            onClick={() => handleStartMission('atmosphere')}
                            className={`bg-warm-cream rounded-[2rem] p-6 shadow-card border border-pale-border transform transition-all duration-300 cursor-pointer hover:border-coral-end/30 hover:shadow-lg active:scale-[0.98] relative z-20 ${isLoading ? 'opacity-70 pointer-events-none' : ''}`}
                        >
                            {isLoading && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm rounded-[2rem] z-10 flex items-center justify-center">
                                    <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">filter_vintage</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">분위기</span>
                            </div>
                            <h3 className="text-dark-teal text-xl font-bold mb-1">분위기 포착</h3>
                            <p className="text-gray-400 text-sm leading-snug">책장에 스며드는 아침 햇살을 사진으로 담아보세요.</p>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
