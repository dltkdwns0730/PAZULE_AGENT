import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMission } from "../hooks/useMission";
import { useMissionStore } from "../store/useMissionStore";

export default function MissionHome() {
    const navigate = useNavigate();
    const { fetchHint, startMission, isLoading } = useMission();
    const { previewHints } = useMissionStore();

    useEffect(() => {
        fetchHint('location', 'guest');
        fetchHint('atmosphere', 'guest');
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

    const VqaChecklist = ({ vqaHints }) => {
        if (!vqaHints || vqaHints.length === 0) return null;
        return (
            <div
                className="bg-dark-teal/5 border border-dark-teal/15 rounded-xl p-3 mt-3"
                onClick={(e) => e.stopPropagation()}
            >
                <p className="text-dark-teal/60 text-[10px] font-bold uppercase tracking-widest mb-2">AI 검증 기준</p>
                <ul className="space-y-1.5">
                    {vqaHints.map((q, i) => (
                        <li key={i} className="flex items-start gap-2">
                            <span className="text-dark-teal/40 text-xs mt-0.5 flex-shrink-0">✓</span>
                            <span className="text-dark-teal/70 text-xs leading-snug">{q}</span>
                        </li>
                    ))}
                </ul>
            </div>
        );
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
                    <div 
                        onClick={() => navigate('/profile')}
                        className="w-10 h-10 rounded-full bg-light-grey flex items-center justify-center border border-gray-100 text-dark-teal shadow-sm cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                        <span className="material-symbols-outlined text-2xl">person</span>
                    </div>
                </header>

                {/* Main Content Scroll */}
                <main className="flex-1 px-6 py-6 overflow-y-auto no-scrollbar bg-white">

                    {/* Active Missions */}
                    <div className="space-y-4 pb-4">
                        <div className="flex justify-between items-end">
                            <h2 className="text-dark-teal font-bold text-lg">미션</h2>
                            <span className="animate-pulse text-coral-end text-xs font-bold uppercase tracking-widest bg-coral-start/10 px-3 py-1.5 rounded-full">2개 진행 중</span>
                        </div>

                        {/* Mission Card 1 — 랜드마크 찾기 */}
                        <div
                            onClick={() => !previewHints.location?.completed && handleStartMission('location')}
                            className={`bg-warm-cream rounded-[2rem] p-6 shadow-[0_10px_30px_-8px_rgba(55,119,113,0.2)] border border-dark-teal/5 transform transition-all duration-300 cursor-pointer hover:border-coral-end/30 hover:shadow-lg active:scale-[0.98] relative z-20 ${isLoading || previewHints.location?.completed ? 'opacity-70 pointer-events-none' : ''}`}
                        >
                            {(isLoading || previewHints.location?.completed) && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm rounded-[2rem] z-10 flex items-center justify-center">
                                    {previewHints.location?.completed ? (
                                        <div className="bg-dark-teal text-white px-4 py-2 rounded-full font-bold text-sm shadow-md animate-scale-in">오늘의 미션 완료!</div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
                                    )}
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">location_on</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">탐험</span>
                            </div>
                            <h3 className="text-dark-teal text-2xl font-extrabold mb-2 tracking-tight">랜드마크 찾기</h3>
                            <p className="text-gray-400 text-sm leading-snug">
                                {previewHints.location?.hint || "오늘의 힌트를 불러오는 중..."}
                            </p>
                            <VqaChecklist vqaHints={previewHints.location?.vqa_hints} />
                        </div>

                        {/* Mission Card 2 — 분위기 담아내기 */}
                        <div
                            onClick={() => !previewHints.atmosphere?.completed && handleStartMission('atmosphere')}
                            className={`bg-warm-cream rounded-[2rem] p-6 shadow-[0_10px_30px_-8px_rgba(55,119,113,0.2)] border border-dark-teal/5 transform transition-all duration-300 cursor-pointer hover:border-coral-end/30 hover:shadow-lg active:scale-[0.98] relative z-20 ${isLoading || previewHints.atmosphere?.completed ? 'opacity-70 pointer-events-none' : ''}`}
                        >
                            {(isLoading || previewHints.atmosphere?.completed) && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm rounded-[2rem] z-10 flex items-center justify-center">
                                    {previewHints.atmosphere?.completed ? (
                                        <div className="bg-dark-teal text-white px-4 py-2 rounded-full font-bold text-sm shadow-md animate-scale-in">오늘의 미션 완료!</div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
                                    )}
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">filter_vintage</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">분위기</span>
                            </div>
                            <h3 className="text-dark-teal text-2xl font-extrabold mb-2 tracking-tight">분위기 담아내기</h3>
                            <p className="text-gray-400 text-sm leading-snug">
                                {previewHints.atmosphere?.hint || "오늘의 힌트를 불러오는 중..."}
                            </p>
                            <VqaChecklist vqaHints={previewHints.atmosphere?.vqa_hints} />
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
