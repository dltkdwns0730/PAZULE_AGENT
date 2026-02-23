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
            alert(error.message || 'Failed to start mission');
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
                        <span className="text-gray-400 text-sm font-medium">Welcome back,</span>
                        <h1 className="text-dark-teal text-2xl font-bold tracking-tight">Hello, Explorer</h1>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-light-grey flex items-center justify-center border border-gray-100 text-dark-teal shadow-sm">
                        <span className="material-symbols-outlined text-2xl">person</span>
                    </div>
                </header>

                {/* Main Content Scroll */}
                <main className="flex-1 px-6 py-6 overflow-y-auto no-scrollbar space-y-6 bg-white">

                    {/* Active Missions */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-end">
                            <h2 className="text-dark-teal font-bold text-lg">Mission</h2>
                            <span className="text-coral-end text-xs font-semibold uppercase tracking-widest bg-pale-coral px-2 py-1 rounded-md">2 Active</span>
                        </div>

                        {/* Mission Card 1 (Location Hunt - Connected to API) */}
                        <div
                            onClick={() => handleStartMission('location')}
                            className={`bg-warm-cream rounded-3xl p-6 shadow-card border border-pale-border transform transition-all duration-300 cursor-pointer hover:border-coral-end/30 hover:shadow-lg active:scale-[0.98] relative z-20 ${isLoading ? 'opacity-70 pointer-events-none' : ''}`}
                        >
                            {isLoading && (
                                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm rounded-3xl z-10 flex items-center justify-center">
                                    <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">location_on</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">Exploration</span>
                            </div>
                            <h3 className="text-dark-teal text-xl font-bold mb-1">Location Hunt</h3>
                            <p className="text-gray-400 text-sm leading-snug">Find the secret courtyard tucked away in the Forest of Wisdom.</p>
                        </div>

                        {/* Mission Card 2 (Atmosphere) */}
                        <div className="bg-warm-cream rounded-3xl p-6 shadow-card border border-pale-border transform transition-transform active:scale-95 cursor-pointer hover:border-coral-end/30 hover:shadow-lg transition-all duration-300">
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-pale-coral rounded-2xl flex items-center justify-center shadow-inner">
                                    <span className="material-symbols-outlined text-coral-end text-3xl">filter_vintage</span>
                                </div>
                                <span className="bg-dark-teal/5 text-dark-teal text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wide">Atmosphere</span>
                            </div>
                            <h3 className="text-dark-teal text-xl font-bold mb-1">Vibe Seeker</h3>
                            <p className="text-gray-400 text-sm leading-snug">Capture a photo of the morning sunlight hitting the book stacks.</p>
                        </div>
                    </div>

                    {/* Today's Hint */}
                    <div className="mt-4 pb-4">
                        <h2 className="text-dark-teal font-bold text-lg mb-3">Today's Hint</h2>
                        <div
                            onClick={() => setIsHintRevealed(true)}
                            className={`bg-light-grey rounded-3xl p-5 relative overflow-hidden cursor-pointer transition-colors border border-gray-100/50 ${isHintRevealed ? 'bg-white shadow-soft pointer-events-none' : 'hover:bg-gray-200 active:bg-gray-300'}`}
                        >
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center shadow-sm transition-colors ${isHintRevealed ? 'bg-coral-end text-white' : 'bg-white text-coral-end'}`}>
                                    <span className="material-symbols-outlined">tips_and_updates</span>
                                </div>
                                <div className="flex-1">
                                    <p className="text-coral-end text-[10px] font-bold uppercase tracking-wider mb-0.5">
                                        {isHintRevealed ? 'Hint Unlocked' : 'Tap to reveal'}
                                    </p>
                                    {!isHintRevealed ? (
                                        <p className="text-gray-600 font-medium text-sm">Where the scent of old paper meets new coffee...</p>
                                    ) : (
                                        <p className="text-dark-teal font-bold text-sm leading-snug animate-fade-in-up">
                                            {hint || "Checking today's hint..."}
                                        </p>
                                    )}
                                </div>
                                {!isHintRevealed && (
                                    <span className="material-symbols-outlined text-gray-300 text-xl">chevron_right</span>
                                )}
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
