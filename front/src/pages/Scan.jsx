import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { useMissionStore } from '../store/useMissionStore';

export default function Scan() {
    const navigate = useNavigate();
    const { coupon } = useMissionStore();

    // Countdown states
    const [timeLeft, setTimeLeft] = useState(0);
    const [theme, setTheme] = useState('light'); // For the toggle

    useEffect(() => {
        if (!coupon) return;

        // 실제 유효기간(7일)이 아닌, 매장 결제용 바코드 표시 타이머(15분)로 동작하게 함
        const timerDuration = 15 * 60; // 15분
        setTimeLeft(timerDuration);

        const timerId = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    clearInterval(timerId);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timerId);
    }, [coupon]);

    const handleGoHome = () => {
        navigate('/');
    };

    const handleSimulateScan = () => {
        if (timeLeft === 0) return;
        alert("🎉 Mock: Coupon scanned successfully at POS!");
        navigate('/wallet');
    };

    if (!coupon) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50">
                <span className="material-symbols-outlined text-4xl text-slate-300 mb-4">qr_code_scanner</span>
                <p className="text-slate-500 font-medium">No active coupon found.</p>
                <button onClick={handleGoHome} className="mt-6 px-6 py-2 bg-[#37776f] text-white rounded-full font-bold">Go Home</button>
            </div>
        );
    }

    // Format time left (MM:SS)
    const minutes = Math.floor(timeLeft / 60).toString().padStart(2, '0');
    const seconds = (timeLeft % 60).toString().padStart(2, '0');
    const isExpiringSoon = timeLeft < 60 && timeLeft > 0;
    const isExpired = timeLeft === 0;

    return (
        <div className={`transition-colors duration-500 ${theme === 'light' ? 'bg-[#f6f7f7]' : 'bg-[#151d1c]'} min-h-screen font-display flex items-center justify-center overflow-hidden w-full relative`}>
            {/* Background elements */}
            <div className={`absolute top-0 w-full h-80 ${theme === 'light' ? 'bg-[#37776f]' : 'bg-[#1a2d2a]'} rounded-b-[3rem] transition-colors duration-500`}></div>
            <div className="absolute top-10 left-10 w-32 h-32 bg-white/5 rounded-full blur-2xl"></div>
            <div className="absolute top-20 right-10 w-40 h-40 bg-white/5 rounded-full blur-3xl"></div>

            <main className="relative z-10 w-full max-w-[420px] h-full min-h-[100dvh] flex flex-col pt-12">
                {/* Header */}
                <header className="px-6 flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur border border-white/30 flex items-center justify-center overflow-hidden shadow-sm">
                            <span className="text-white font-bold text-sm">JD</span>
                        </div>
                        <div>
                            <p className="text-white/80 text-xs font-medium">Wallet</p>
                            <p className="text-white font-bold tracking-tight">Forest of Wisdom</p>
                        </div>
                    </div>
                    {/* Theme Toggle */}
                    <button
                        onClick={() => setTheme(prev => prev === 'light' ? 'dark' : 'light')}
                        className={`w-14 h-8 rounded-full p-1 transition-colors relative flex items-center ${theme === 'light' ? 'bg-white/20' : 'bg-[#37776f]'}`}
                    >
                        <div className={`w-6 h-6 rounded-full bg-white shadow-md flex items-center justify-center transition-transform duration-300 ${theme === 'light' ? 'translate-x-0' : 'translate-x-6'}`}>
                            <span className={`material-symbols-outlined text-[14px] ${theme === 'light' ? 'text-amber-500' : 'text-[#37776f]'}`}>
                                {theme === 'light' ? 'light_mode' : 'dark_mode'}
                            </span>
                        </div>
                    </button>
                </header>

                <div className="flex-1 w-full px-4 sm:px-6 relative flex flex-col items-center overflow-y-auto no-scrollbar pb-12">
                    {/* Main Coupon Card */}
                    <div className={`w-full bg-white rounded-[2rem] shadow-2xl overflow-hidden flex flex-col shrink-0 mt-8 sm:mt-12 ${isExpired ? 'opacity-75 grayscale sepia-0' : ''}`}>

                        {/* Card Header (Store Details) */}
                        <div className="p-6 pb-0 flex flex-col items-center relative">
                            {/* Decorative Notches */}
                            <div className={`absolute top-1/2 -left-3 w-6 h-6 rounded-full ${theme === 'light' ? 'bg-[#f6f7f7]' : 'bg-[#151d1c]'}`}></div>
                            <div className={`absolute top-1/2 -right-3 w-6 h-6 rounded-full ${theme === 'light' ? 'bg-[#f6f7f7]' : 'bg-[#151d1c]'}`}></div>

                            <h2 className="text-xl font-bold text-slate-900 mt-4 mb-1">10% OFF COFFEE</h2>
                            <p className="text-sm font-medium text-slate-500 mb-6 text-center max-w-[220px]">
                                {coupon.description || 'Present this QR code at the counter.'}
                            </p>

                            {/* Divider */}
                            <div className="w-full flex items-center justify-between mb-6">
                                <div className={`w-full border-t-2 border-dashed ${theme === 'light' ? 'border-slate-200' : 'border-slate-200'} relative`}></div>
                            </div>
                        </div>

                        {/* QR Code Section */}
                        <div className="px-6 pb-6 flex flex-col items-center">
                            {/* QR Frame Container */}
                            <div 
                                onClick={handleSimulateScan}
                                className={`relative p-2 bg-gradient-to-br from-slate-100 to-slate-50 border border-slate-200 rounded-[24px] shadow-inner mb-6 group transition-transform ${isExpired ? '' : 'cursor-pointer hover:scale-105 active:scale-95'}`}
                                title={isExpired ? "QR Code Expired" : "클릭하여 POS 스캔 시뮬레이션"}
                            >
                                {/* The actual scanning area */}
                                <div className={`p-4 bg-white rounded-[16px] shadow-sm relative overflow-hidden ${isExpired ? 'opacity-50' : ''}`}>
                                    {/* Scanning laser animation */}
                                    {!isExpired && (
                                        <div className="absolute top-0 left-0 w-full h-[2px] bg-[#37776f]/40 shadow-[0_0_8px_2px_rgba(55,119,111,0.4)] animate-[scan_2.5s_ease-in-out_infinite]"></div>
                                    )}
                                    <QRCodeSVG value={coupon.code} size={180} level="H" includeMargin={false} fgColor="#111717" />
                                </div>
                                {isExpired && (
                                    <div className="absolute inset-0 z-10 flex items-center justify-center">
                                        <div className="bg-red-500 text-white font-bold py-1 px-4 rounded-full shadow-lg transform -rotate-12">
                                            EXPIRED
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Coupon Code Display */}
                            <div className="bg-slate-50 px-5 py-2.5 rounded-full border border-slate-100 mb-6">
                                <p className="font-mono text-lg font-bold tracking-widest text-[#37776f] select-all">
                                    {coupon.code}
                                </p>
                            </div>

                            {/* Countdown Timer */}
                            <div className="w-full flex justify-between items-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                <div>
                                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-0.5">Time Remaining</p>
                                    <p className={`text-2xl font-black tabular-nums tracking-tight ${isExpiringSoon ? 'text-red-500 animate-pulse' : 'text-slate-800'}`}>
                                        {minutes}:{seconds}
                                    </p>
                                </div>
                                <div className={`size-12 rounded-full flex items-center justify-center ${isExpiringSoon ? 'bg-red-50' : 'bg-[#4ce0b3]/10'}`}>
                                    <span className={`material-symbols-outlined text-[24px] ${isExpiringSoon ? 'text-red-500 animate-[pulse-ring_1.5s_infinite]' : 'text-[#37776f]'}`}>
                                        {isExpired ? 'timer_off' : 'timer'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Decorative blurred blob underneath card */}
                    <div className="absolute -bottom-10 w-full h-20 bg-black/10 blur-xl rounded-full z-0 pointer-events-none"></div>
                </div>

                {/* Blank space to account for fixed bottom nav */}
                <div className="h-20 w-full shrink-0"></div>
            </main>
        </div>
    );
}
