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
            alert(error.message || '쿠폰 발급에 실패했습니다');
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
                <p>결과가 없습니다. 먼저 미션을 시작하세요.</p>
                <button onClick={handleClose} className="ml-4 text-blue-500 underline">홈으로</button>
            </div>
        );
    }

    const { success, score, message, error } = submissionResult;
    const isSuccess = success;
    const matchPercentage = score !== undefined ? (score * 100).toFixed(0) : (isSuccess ? '100' : '0');

    if (isSuccess) {
        return (
            <div className="font-display h-full w-full flex flex-col relative bg-[#f0f2f5] dark:bg-background-dark antialiased">
                <main className="relative w-full h-full flex flex-col bg-gradient-to-b from-[#f0fdf9] to-white dark:bg-gradient-to-b dark:from-[#0f3a37] dark:to-[#1a2827] overflow-hidden shadow-2xl">
                    {/* Background Layer with Blur */}
                    <div className="absolute inset-0 z-0">
                        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuADGds8xEZ3vhewFrS-xWCwPy0upBbCs0--yUG0y1n2mkQarnzT0QUn4PA3drjvqqM8xx3s9OZjM-mWRNC8vw-aIfzpwv_ip5OraxAxTiOtt2q8tDmJohDyhpKGkELk31yAguTtvaPa-uJXt3U9vVOVlTX593ADfg-MYgcB-vIeMH7eIQtI-VziOJeSyOZCKPuYyF6DaCz-lXqj-iTIklZ0upzyby_RlV0i2S7FQVptZMRwGt_OpFjcgrleKQCt5ZbBzD7ehj0z4B0')" }}></div>
                        <div className="absolute inset-0 bg-white/90 backdrop-blur-md"></div>
                    </div>

                    {/* Content Layer */}
                    <div className="relative z-10 flex flex-col h-full">
                        {/* Header */}
                        <header className="flex items-center justify-end px-6 pt-12 pb-2">
                            <button onClick={handleClose} className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-100/50 hover:bg-slate-200 text-[#37776f] transition-colors">
                                <span className="material-symbols-outlined text-2xl font-bold">close</span>
                            </button>
                        </header>

                        {/* Main Content Area */}
                        <div className="flex-1 overflow-y-auto no-scrollbar px-6 flex flex-col items-center pb-28">
                            {/* Success Indicator */}
                            <div className="relative flex items-center justify-center w-32 h-32 mb-6 mt-4">
                                <div className="absolute inset-0 rounded-full bg-[#4ce0b3] opacity-10 animate-[subtle-pulse_3s_infinite_ease-in-out]"></div>
                                <div className="w-20 h-20 bg-[#4ce0b3] rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(76,224,179,0.5)] animate-scale-in transform transition-transform duration-700 hover:scale-105">
                                    <span className="material-symbols-outlined text-white text-[40px] font-bold">check</span>
                                </div>
                            </div>

                            {/* Headline */}
                            <div className="text-center mb-8">
                                <h1 className="text-[32px] font-bold text-[#37776f] leading-tight mb-3 tracking-tight">미션 성공!</h1>
                                <p className="text-slate-500 text-base font-medium leading-relaxed max-w-[280px] mx-auto">
                                    {message || "잘했어요! AI가 사진을 분석하고 위치를 확인했습니다."}
                                </p>
                            </div>

                            {/* AI Analysis Card */}
                            <div className="w-full bg-white rounded-[1.5rem] shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] p-6 mb-4 border border-slate-100/50">
                                <div className="flex items-center justify-between mb-4 border-b border-slate-50 pb-3">
                                    <div className="flex items-center gap-2 text-[#37776f]">
                                        <span className="material-symbols-outlined filled font-variation-settings-'FILL' 1;">psychology</span>
                                        <span className="text-sm font-bold tracking-tight">AI 분석 결과</span>
                                    </div>
                                    <div className="px-2.5 py-0.5 bg-[#4ce0b3]/20 rounded-full flex items-center">
                                        <span className="text-[10px] font-bold text-teal-700 tracking-wider">확인됨</span>
                                    </div>
                                </div>

                                <div className="flex gap-6 items-center mb-4">
                                    <div className="flex-shrink-0 relative w-24 h-24 flex items-center justify-center">
                                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                                            <circle cx="60" cy="60" r="45" fill="none" stroke="rgba(203, 213, 225, 0.5)" strokeWidth="4" />
                                            <circle
                                                cx="60" cy="60" r="45" fill="none" stroke="#4ce0b3" strokeWidth="4" strokeLinecap="round"
                                                style={{
                                                    strokeDasharray: 282.74,
                                                    strokeDashoffset: 282.74 * (1 - matchPercentage / 100),
                                                    transition: 'stroke-dashoffset 1s ease-out',
                                                }}
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <span className="text-2xl font-extrabold text-slate-900">{matchPercentage}</span>
                                            <span className="text-xs font-bold text-slate-400">%</span>
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-bold text-slate-700 mb-2">일치도</p>
                                        <p className="text-xs text-slate-500 leading-snug">건축 특징이 참조 이미지와 완벽하게 일치합니다.</p>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="flex flex-col gap-2">
                                    <div className="flex justify-between items-end text-xs">
                                        <span className="text-slate-400 font-medium">신뢰도</span>
                                        <span className="text-[#37776f] font-bold">{matchPercentage >= 80 ? '높음' : '중간'}</span>
                                    </div>
                                    <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-[#4ce0b3] rounded-full shadow-[0_0_10px_rgba(76,224,179,0.5)] transition-all duration-1000" style={{ width: `${matchPercentage}%` }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Bottom Fixed Action */}
                        <div className="absolute bottom-0 left-0 right-0 p-6 pt-12 pb-8 bg-gradient-to-t from-white via-white/95 to-transparent pointer-events-none">
                            <button
                                onClick={handleIssueCoupon}
                                disabled={isLoading}
                                className={`w-full pointer-events-auto bg-[#37776f] hover:bg-[#2a5c55] text-white font-bold h-14 rounded-2xl shadow-lg shadow-[#37776f]/20 flex items-center justify-center gap-2 active:scale-[0.98] transition-all ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
                            >
                                <span className="text-[17px] tracking-wide">{isLoading ? '발급 중...' : '쿠폰 발급'}</span>
                                <span className="material-symbols-outlined">confirmation_number</span>
                            </button>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    // Failure State
    return (
        <div className="font-display h-full w-full flex flex-col relative bg-[#f6f7f7] antialiased">
            <div className="absolute inset-0 bg-cover bg-center opacity-30 z-0" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCykysqkXemm4SBjI7XHqjHK7wEo9OA5ypcifOW4_LtQtXwtI_T6jVquv7c8AWMZmd1YuaqEdsdAdOs3lt6zSygnZca9DiN2IZFCfO90TlOqywp8gidTzMTFC-uyHeWcJncgxDAn_lwqx_1x1lPp3lI7mE8sr6O_o9CTmu3_59crWxPF44Ml0YNhOwBeNk49FFfRcPKj_ul2HKztW3UbDybQW_QvfaA1u8F80NwBO-phjNsX-tJ-rBtwN_a5F1ZGs8oGbwg25DH9hE')" }}></div>
            <div className="absolute inset-0 bg-[#37776f]/10 backdrop-blur-3xl z-0"></div>

            <main className="relative z-10 w-full h-full bg-gradient-to-b from-[#fff5f3] to-[#f6f7f7] dark:bg-gradient-to-b dark:from-[#3a1915] dark:to-[#1a2322] shadow-2xl flex flex-col border border-white/20">
                {/* Top Nav: Close Button */}
                <div className="flex justify-end pt-12 px-6 pb-2">
                    <button onClick={handleClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-black/5 hover:bg-black/10 active:scale-95 transition-all text-[#111717]">
                        <span className="material-symbols-outlined text-xl">close</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col px-6 pb-28 relative">
                    {/* Hero Section */}
                    <div className="flex flex-col items-center text-center mt-6 mb-10">
                        <div className="relative flex items-center justify-center w-28 h-28 mb-6">
                            <div className="absolute inset-0 rounded-full bg-[#ed6a5e] opacity-10 animate-subtle-pulse"></div>
                            <div className="w-20 h-20 bg-[#ed6a5e]/10 rounded-full flex items-center justify-center animate-scale-in shadow-[0_0_20px_rgba(237,106,94,0.3)]">
                                <span className="material-symbols-outlined text-[#ed6a5e] text-[40px] font-bold">close</span>
                            </div>
                        </div>
                        <h1 className="text-[#37776f] text-[28px] font-bold leading-tight mb-3 tracking-tight">인증 실패</h1>
                        <p className="text-slate-500 text-base font-medium leading-relaxed max-w-[280px]">
                            {message || error || "대상을 찾을 수 없습니다. 사진에서 예상되는 특정 기능을 식별할 수 없었습니다."}
                        </p>
                    </div>

                    {/* AI Analysis Card */}
                    <div className="w-full bg-white rounded-[1.5rem] p-6 shadow-[0_20px_40px_-4px_rgba(0,0,0,0.05)] mb-6 border border-slate-100">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <p className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-1">AI 일치도</p>
                                <p className="text-[#ed6a5e] text-4xl font-extrabold tracking-tight">{matchPercentage}%</p>
                            </div>
                            <div className="bg-[#ed6a5e]/10 text-[#ed6a5e] px-3 py-1 rounded-full text-[11px] font-bold tracking-widest">신뢰도 낮음</div>
                        </div>
                        <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden mb-5 border border-slate-200/50">
                            <div className="h-full bg-[#ed6a5e] transition-all duration-1000" style={{ width: `${matchPercentage}%` }}></div>
                        </div>
                        <div className="flex gap-3 items-start bg-red-50/50 p-4 rounded-xl border border-red-100/30">
                            <span className="material-symbols-outlined text-[#ed6a5e] text-[20px] mt-0.5 opacity-80">info</span>
                            <p className="text-slate-600 text-sm font-medium leading-snug">
                                세부사항: 이미지가 너무 흐릿하거나 어둡거나 정확한 각도가 없을 수 있습니다.
                            </p>
                        </div>
                    </div>

                    {/* Hint / Attempts */}
                    <div className="flex flex-col items-center justify-center mt-auto pb-4 space-y-3">
                        <div className="flex items-center gap-2 text-[#ed6a5e] font-bold bg-[#ed6a5e]/5 px-5 py-2.5 rounded-full border border-[#ed6a5e]/10">
                            <span className="material-symbols-outlined text-[20px]">warning</span>
                            <span className="text-sm tracking-wide">다시 시도하세요</span>
                        </div>
                        <p className="text-slate-400 text-xs text-center px-6 leading-relaxed">대상이 충분히 밝고 프레임 내에서 완전히 보이는지 확인하세요.</p>
                    </div>
                </div>

                {/* Sticky Bottom Action */}
                <div className="absolute bottom-0 left-0 right-0 p-6 pb-8 pt-12 bg-gradient-to-t from-[#f6f7f7] via-[#f6f7f7]/95 to-transparent pointer-events-none">
                    <button onClick={handleTryAgain} className="w-full pointer-events-auto bg-[#37776f] hover:bg-[#2a5c55] active:scale-[0.98] transition-all h-14 rounded-2xl flex items-center justify-center gap-2 shadow-[0_12px_24px_-6px_rgba(55,119,111,0.15)] group relative overflow-hidden">
                        <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <span className="material-symbols-outlined text-white group-hover:rotate-180 transition-transform duration-700">refresh</span>
                        <span className="text-white text-[17px] font-bold tracking-wide">다시 시도</span>
                    </button>
                </div>
            </main>
        </div>
    );
}
