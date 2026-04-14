import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMission } from '../hooks/useMission';
import { useMissionStore } from '../store/useMissionStore';
import AILoadingOverlay from '../components/AILoadingOverlay';

const MAX_ATTEMPTS = 3;

export default function PhotoSubmission() {
    const navigate = useNavigate();
    const { submitPhoto, isLoading } = useMission();
    const store = useMissionStore();

    const [imageFile, setImageFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [retryError, setRetryError] = useState(null);
    const [attemptsLeft, setAttemptsLeft] = useState(MAX_ATTEMPTS);
    const fileInputRef = useRef(null);

    // Route guard: 활성 mission 없이 접근 시 홈으로 redirect
    useEffect(() => {
        if (!store.missionId) {
            navigate('/');
        }
    }, [store.missionId]);

    // Current Date formatting
    const today = new Date();
    const dateFormatted = `${today.toLocaleString('en-US', { month: 'short' })} ${today.getDate()}, ${today.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} (Today)`;

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            setPreviewUrl(URL.createObjectURL(file));
            setRetryError(null);
        }
    };

    const handleUploadClick = () => {
        if (!isLoading) {
            fileInputRef.current.click();
        }
    };

    const handleSubmit = async () => {
        if (!imageFile) return;

        try {
            const result = await submitPhoto(imageFile);
            if (result.success) {
                navigate('/mission/result');
            } else {
                const newAttemptsLeft = Math.max(0, attemptsLeft - 1);
                setAttemptsLeft(newAttemptsLeft);
                setRetryError(result.error || result.message || 'Verification Failed. Target not found.');

                if (newAttemptsLeft <= 0) {
                    navigate('/mission/result'); // Go to failure result if out of attempts
                }
            }
        } catch (err) {
            setRetryError(err.message || 'Server connection failed.');
        }
    };

    return (
        <div className="font-display h-full w-full flex flex-col relative bg-[#f0f2f5] dark:bg-background-dark antialiased selection:bg-primary/20">

            {/* Background Blur Elements */}
            <div className="fixed inset-0 z-0 bg-slate-100 dark:bg-background-dark flex items-center justify-center opacity-40 overflow-hidden pointer-events-none">
                <div className="absolute w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl -top-40 -right-40"></div>
                <div className="absolute w-[600px] h-[600px] bg-accent-orange/5 rounded-full blur-3xl bottom-0 left-0"></div>
            </div>

            <main className="relative w-full h-full bg-bg-soft dark:bg-[#1a2322] flex flex-col shrink-0 z-10 overflow-hidden">

                {/* --- RETRY BANNER --- */}
                <div className={`absolute top-0 left-0 w-full z-50 transform ${retryError ? 'translate-y-0' : '-translate-y-full'} transition-transform duration-300 ease-in-out bg-red-50 p-4 pt-12 pb-4 shadow-sm border-b border-red-100 flex items-center justify-between gap-3`}>
                    <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-red-500">error</span>
                        <div>
                            <p className="text-red-900 text-sm font-bold">Verification failed</p>
                            <p className="text-red-700 text-xs">{attemptsLeft} attempts left</p>
                        </div>
                    </div>
                    <button onClick={() => setRetryError(null)} className="px-3 py-1.5 bg-red-100 text-red-700 text-xs font-bold rounded-lg hover:bg-red-200 transition-colors">
                        Dismiss
                    </button>
                </div>

                {/* --- AI ANALYSIS OVERLAY --- */}
                <AILoadingOverlay isVisible={isLoading} />

                {/* Header */}
                <header className="flex items-center justify-between px-5 py-2 mt-4 z-20">
                    <button onClick={() => navigate(-1)} className="flex h-10 w-10 items-center justify-center rounded-full text-slate-800 hover:bg-black/5 dark:text-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <span className="material-symbols-outlined">arrow_back_ios_new</span>
                    </button>
                    <span className="text-slate-800 dark:text-slate-100 font-bold text-base tracking-tight">Mission Detail</span>
                    <button onClick={() => navigate('/')} className="flex h-10 w-10 items-center justify-center rounded-full text-slate-800 hover:bg-black/5 dark:text-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto px-5 pt-2 pb-28 no-scrollbar relative z-10">
                    <div className="bg-glass-surface backdrop-blur-md border border-white/60 shadow-[0_8px_32px_0_rgba(31,38,135,0.05)] rounded-3xl p-1 mb-6">
                        <div className="bg-white/40 dark:bg-black/20 rounded-[1.4rem] p-6 flex flex-col items-center text-center">
                            <div className="inline-flex items-center justify-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary mb-4">
                                <span className="material-symbols-outlined text-[16px]">location_on</span>
                                <span className="text-[11px] font-bold uppercase tracking-wider">Mission Target</span>
                            </div>
                            <h1 className="text-[26px] font-extrabold text-slate-800 dark:text-white leading-tight mb-2 tracking-tight">
                                {store.missionId === 'location' ? <>Find the<br />Giant Bookshelf</> : <>Capture the<br />Atmosphere</>}
                            </h1>
                            <p className="text-slate-500 dark:text-slate-300 text-sm font-medium leading-relaxed max-w-[260px] mx-auto mb-6">
                                {store.hint || "Verify your visit to unlock the reward coupon."}
                            </p>

                            {/* Upload Area */}
                            <div className="relative w-full aspect-square group cursor-pointer" onClick={handleUploadClick}>
                                <div className={`absolute inset-0 rounded-[2rem] border-2 border-dashed ${previewUrl ? 'border-transparent' : 'border-slate-300/80 dark:border-slate-600 bg-white/60 dark:bg-slate-800/50 shadow-[inset_0_0_40px_0_rgba(255,175,135,0.15)]'} flex flex-col items-center justify-center gap-4 transition-all duration-300 group-hover:border-accent-orange/50 group-hover:bg-white/80 dark:group-hover:bg-slate-800 overflow-hidden`}>
                                    {!previewUrl && (
                                        <>
                                            <div className="absolute inset-0 bg-gradient-to-tr from-accent-glow/5 to-transparent opacity-50 pointer-events-none"></div>
                                            <div className="relative h-20 w-20 rounded-full bg-gradient-to-br from-white to-orange-50 border border-orange-100/50 flex items-center justify-center shadow-lg shadow-orange-100 group-hover:scale-105 transition-transform duration-300">
                                                <span className="material-symbols-outlined text-[36px] text-accent-orange">photo_camera</span>
                                            </div>
                                            <div className="relative text-center z-10">
                                                <p className="text-slate-800 dark:text-slate-100 font-bold text-lg">Tap to take photo</p>
                                                <p className="text-slate-400 text-xs mt-1">or upload from gallery</p>
                                            </div>
                                        </>
                                    )}
                                </div>
                                {previewUrl && (
                                    <img
                                        src={previewUrl}
                                        alt="Upload Preview"
                                        className="absolute inset-0 h-full w-full object-cover rounded-[2rem] pointer-events-none transition-opacity duration-300"
                                    />
                                )}
                            </div>
                            <input
                                type="file"
                                accept="image/*"
                                className="hidden"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                            />
                        </div>
                    </div>

                    <div className="space-y-3 px-1">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-2">Verification Steps</h3>

                        <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl shadow-sm">
                            <div className="flex items-center gap-3.5">
                                <div className="h-10 w-10 rounded-full bg-[#f0fdf9] flex items-center justify-center text-primary border border-primary/10">
                                    <span className="material-symbols-outlined text-[20px]">near_me</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-bold text-slate-800 dark:text-slate-100">GPS Location</span>
                                    <span className="text-xs text-primary/80 font-medium">Verified Contextually</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-center h-6 w-6 rounded-full bg-accent-mint text-white">
                                <span className="material-symbols-outlined text-[16px] font-bold">check</span>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-white/60 dark:bg-slate-800/60 border border-slate-100/50 dark:border-slate-700 rounded-2xl">
                            <div className="flex items-center gap-3.5">
                                <div className="h-10 w-10 rounded-full bg-white dark:bg-slate-700 flex items-center justify-center text-primary border border-slate-100 dark:border-slate-600">
                                    <span className="material-symbols-outlined text-[20px]">schedule</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-bold text-slate-800 dark:text-slate-100">Current Time</span>
                                    <span className="text-xs text-slate-400">{imageFile ? dateFormatted : 'Waiting for photo...'}</span>
                                </div>
                            </div>
                            {imageFile ? (
                                <div className="flex items-center justify-center h-6 w-6 rounded-full bg-accent-mint text-white">
                                    <span className="material-symbols-outlined text-[16px] font-bold">check</span>
                                </div>
                            ) : (
                                <div className="h-5 w-5 rounded-full border-[2.5px] border-slate-200 dark:border-slate-600"></div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom Action Bar */}
                <div className="absolute bottom-0 left-0 right-0 px-6 pb-8 pt-12 bg-gradient-to-t from-bg-soft via-bg-soft/95 to-transparent dark:from-[#1a2322] dark:via-[#1a2322]/95 z-40 pointer-events-none">
                    <div className="pointer-events-auto">
                        <button
                            onClick={handleSubmit}
                            disabled={!imageFile || isLoading}
                            className={`w-full h-[3.75rem] transition-all rounded-2xl flex items-center justify-center gap-2 border border-white/10 ${imageFile && !isLoading ? 'bg-primary hover:bg-primary-dark active:scale-[0.98] shadow-[0_15px_30px_-8px_rgba(55,119,113,0.4)]' : 'bg-slate-300 opacity-70 cursor-not-allowed shadow-none'}`}
                        >
                            <span className="text-white font-bold text-[17px] tracking-wide">Submit for Verification</span>
                        </button>
                    </div>
                </div>

            </main>
        </div>
    );
}
