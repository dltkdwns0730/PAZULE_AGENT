import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMissionStore } from '../store/useMissionStore';
import { useMission } from '../hooks/useMission';

export default function MissionResult() {
    const navigate = useNavigate();
    const { submissionResult } = useMissionStore();
    const { issueCoupon, isLoading } = useMission();

    const handleIssueCoupon = async () => {
        try {
            await issueCoupon();
            navigate('/coupon/success');
        } catch (error) {
            alert(error.message || 'Failed to issue coupon');
        }
    };

    const handleTryAgain = () => {
        navigate('/mission/submit');
    };

    const handleClose = () => {
        navigate('/');
    };

    // If no result is found (e.g. user refreshed the page), provide fallback or redirect
    if (!submissionResult) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <p>No result available. Please start a mission first.</p>
                <button onClick={handleClose} className="ml-4 text-blue-500 underline">Go Home</button>
            </div>
        );
    }

    const { success, score, message, error } = submissionResult;
    const isSuccess = success;
    const matchPercentage = score !== undefined ? (score * 100).toFixed(0) : (isSuccess ? '100' : '0');

    if (isSuccess) {
        return (
            <div className="bg-slate-100 flex items-center justify-center min-h-screen p-4 sm:p-8 font-display">
                <div className="relative w-full max-w-[400px] h-screen max-h-[850px] bg-white rounded-[2.5rem] overflow-hidden shadow-2xl border-8 border-slate-900 flex flex-col group/design-root">
                    {/* Background Layer with Blur */}
                    <div className="absolute inset-0 z-0">
                        {/* Placeholder bg as shown in design */}
                        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuADGds8xEZ3vhewFrS-xWCwPy0upBbCs0--yUG0y1n2mkQarnzT0QUn4PA3drjvqqM8xx3s9OZjM-mWRNC8vw-aIfzpwv_ip5OraxAxTiOtt2q8tDmJohDyhpKGkELk31yAguTtvaPa-uJXt3U9vVOVlTX593ADfg-MYgcB-vIeMH7eIQtI-VziOJeSyOZCKPuYyF6DaCz-lXqj-iTIklZ0upzyby_RlV0i2S7FQVptZMRwGt_OpFjcgrleKQCt5ZbBzD7ehj0z4B0')" }}></div>
                        <div className="absolute inset-0 bg-white/90 backdrop-blur-md"></div>
                    </div>

                    {/* Content Layer */}
                    <div className="relative z-10 flex flex-col h-full overflow-y-auto no-scrollbar">
                        {/* Header */}
                        <header className="flex items-center justify-end px-6 pt-12 pb-2">
                            <button onClick={handleClose} className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 text-[#37776f] transition-colors">
                                <span className="material-symbols-outlined text-2xl font-bold">close</span>
                            </button>
                        </header>

                        {/* Main Content Area */}
                        <main className="flex-1 px-6 flex flex-col items-center pb-24">
                            {/* Success Indicator */}
                            <div className="relative flex items-center justify-center w-32 h-32 mb-4 mt-2">
                                <div className="absolute inset-0 rounded-full bg-[#4ce0b3] opacity-10 animate-[subtle-pulse_3s_infinite_ease-in-out]"></div>
                                <div className="w-20 h-20 bg-[#4ce0b3] rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(76,224,179,0.4)] transform transition-transform duration-700 hover:scale-105">
                                    <span className="material-symbols-outlined text-white text-[40px] font-bold">check</span>
                                </div>
                            </div>

                            {/* Headline */}
                            <div className="text-center mb-8">
                                <h1 className="text-[32px] font-bold text-[#37776f] leading-tight mb-2 tracking-tight">Mission Complete!</h1>
                                <p className="text-slate-500 text-sm font-medium leading-relaxed max-w-[280px] mx-auto">
                                    {message || "Great job! The AI has analyzed your photo and verified the location."}
                                </p>
                            </div>

                            {/* AI Analysis Card */}
                            <div className="w-full bg-white rounded-2xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] p-5 mb-4 border border-slate-100/50">
                                <div className="flex items-center justify-between mb-4 border-b border-slate-50 pb-3">
                                    <div className="flex items-center gap-2 text-[#37776f]">
                                        <span className="material-symbols-outlined filled font-variation-settings-'FILL' 1;">psychology</span>
                                        <span className="text-sm font-bold tracking-tight">AI Analysis Result</span>
                                    </div>
                                    <div className="px-2.5 py-0.5 bg-[#4ce0b3]/20 rounded-full flex items-center">
                                        <span className="text-[10px] font-bold text-teal-700 tracking-wider">VERIFIED</span>
                                    </div>
                                </div>

                                <div className="flex gap-4 items-start mb-4">
                                    <div className="w-16 h-16 rounded-lg bg-slate-100 overflow-hidden shrink-0 border border-slate-200">
                                        <div className="w-full h-full bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCcp1ro4FZ_4o3OsCKFIgVZ9mpwidkM7XBcDrLUUfrlGwUqZAQ2O3rhmYAwRFRdtvmpPycESKjJehOFsNByWCHDohyKmU2O0J_NnaVbnFNfhJh70DIpVgA8Df3Tkq3gPXK2W9WQOYTekhbj5YX5rYoGMYjMeTHYNhuma6_I-pvjjMIvodVe02MmSKv154nPaqEye1sq2OZou6TwFK6hue0mAQAeVXOrmzT1G3iELYiQF_r_yVdQR3pwq_8aZd4WQmycgejhiirSGRk')" }}></div>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-baseline gap-1 mb-1">
                                            <span className="text-4xl font-extrabold text-slate-900 tracking-tight">{matchPercentage}</span>
                                            <span className="text-lg font-bold text-slate-400">%</span>
                                            <span className="text-sm font-semibold text-slate-400 ml-1">Match</span>
                                        </div>
                                        <p className="text-xs text-slate-500 leading-snug">The architectural features match the reference perfectly.</p>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="flex flex-col gap-2">
                                    <div className="flex justify-between items-end text-xs">
                                        <span className="text-slate-400 font-medium">Confidence Score</span>
                                        <span className="text-[#37776f] font-bold">{matchPercentage >= 80 ? 'High' : 'Medium'}</span>
                                    </div>
                                    <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-[#4ce0b3] rounded-full shadow-[0_0_10px_rgba(76,224,179,0.5)] transition-all duration-1000" style={{ width: `${matchPercentage}%` }}></div>
                                    </div>
                                </div>
                            </div>

                        </main>

                        {/* Bottom Fixed Action */}
                        <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-white via-white to-transparent pt-12">
                            <button
                                onClick={handleIssueCoupon}
                                disabled={isLoading}
                                className={`w-full bg-[#37776f] hover:bg-[#2a5c55] text-white font-bold h-14 rounded-xl shadow-lg shadow-[#37776f]/20 flex items-center justify-center gap-2 active:scale-[0.98] transition-all ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
                            >
                                <span>{isLoading ? 'Issuing...' : 'Issue Coupon'}</span>
                                <span className="material-symbols-outlined">confirmation_number</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Failure State
    return (
        <div className="bg-gray-100 font-display min-h-screen flex items-center justify-center overflow-hidden relative" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCykysqkXemm4SBjI7XHqjHK7wEo9OA5ypcifOW4_LtQtXwtI_T6jVquv7c8AWMZmd1YuaqEdsdAdOs3lt6zSygnZca9DiN2IZFCfO90TlOqywp8gidTzMTFC-uyHeWcJncgxDAn_lwqx_1x1lPp3lI7mE8sr6O_o9CTmu3_59crWxPF44Ml0YNhOwBeNk49FFfRcPKj_ul2HKztW3UbDybQW_QvfaA1u8F80NwBO-phjNsX-tJ-rBtwN_a5F1ZGs8oGbwg25DH9hE')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
            <div className="absolute inset-0 bg-[#37776f]/20 backdrop-blur-xl z-0"></div>

            <main className="relative z-10 w-full max-w-[400px] h-[85vh] max-h-[850px] bg-[#f6f7f7] shadow-2xl rounded-[2.5rem] overflow-hidden flex flex-col border-[8px] border-white/20">

                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col p-6 relative">
                    {/* Top Nav: Close Button */}
                    <div className="flex justify-end mb-4">
                        <button onClick={handleClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-black/5 hover:bg-black/10 active:scale-95 transition-all text-[#111717]">
                            <span className="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    {/* Hero Section */}
                    <div className="flex flex-col items-center text-center mt-2 mb-8">
                        <div className="w-24 h-24 rounded-full bg-[#ed6a5e]/10 flex items-center justify-center mb-6 animate-pulse">
                            <span className="material-symbols-outlined text-[#ed6a5e] text-[48px] font-bold">close</span>
                        </div>
                        <h1 className="text-[#37776f] text-[28px] font-bold leading-tight mb-3">Verification Failed</h1>
                        <p className="text-slate-500 text-base font-medium leading-relaxed max-w-[280px]">
                            {message || error || "Target not found. We couldn't identify the specific expected features in your photo."}
                        </p>
                    </div>

                    {/* AI Analysis Card */}
                    <div className="w-full bg-white rounded-[1.5rem] p-6 shadow-[0_20px_40px_-4px_rgba(0,0,0,0.08)] mb-6 border border-slate-100">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <p className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-1">AI Match Score</p>
                                <p className="text-[#ed6a5e] text-4xl font-extrabold tracking-tight">{matchPercentage}%</p>
                            </div>
                            <div className="bg-[#ed6a5e]/10 text-[#ed6a5e] px-3 py-1 rounded-full text-xs font-bold">Low Confidence</div>
                        </div>
                        <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden mb-4">
                            <div className="h-full bg-[#ed6a5e] rounded-full transition-all duration-1000" style={{ width: `${matchPercentage}%` }}></div>
                        </div>
                        <div className="flex gap-3 items-start bg-slate-50 p-3 rounded-xl">
                            <span className="material-symbols-outlined text-slate-400 text-[20px] mt-0.5">info</span>
                            <p className="text-slate-600 text-sm font-medium leading-snug">
                                Detail: The image might be too blurry, dark, or not capturing the exact required perspective.
                            </p>
                        </div>
                    </div>

                    {/* Hint / Attempts */}
                    <div className="flex flex-col items-center justify-center mt-auto pb-4 space-y-2">
                        <div className="flex items-center gap-2 text-[#ed6a5e] font-bold bg-[#ed6a5e]/5 px-4 py-2 rounded-full">
                            <span className="material-symbols-outlined text-[18px]">warning</span>
                            <span>Please try again</span>
                        </div>
                        <p className="text-slate-400 text-xs text-center px-8">Make sure the target is well-lit and fully visible within the frame.</p>
                    </div>
                </div>

                {/* Sticky Bottom Action */}
                <div className="p-6 pt-2 bg-gradient-to-t from-[#f6f7f7] via-[#f6f7f7] to-transparent">
                    <button onClick={handleTryAgain} className="w-full bg-[#37776f] hover:bg-[#2a5c55] active:scale-[0.98] transition-all h-14 rounded-2xl flex items-center justify-center gap-2 shadow-[0_12px_24px_-6px_rgba(55,119,111,0.15)] group">
                        <span className="material-symbols-outlined text-white group-hover:rotate-180 transition-transform duration-500">refresh</span>
                        <span className="text-white text-lg font-bold">Try Again</span>
                    </button>
                </div>
            </main>
        </div>
    );
}
