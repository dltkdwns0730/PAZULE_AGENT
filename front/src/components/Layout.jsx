import React from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";

export default function Layout() {
    const navigate = useNavigate();
    const location = useLocation();

    // Check if we are on screens that shouldn't show the bottom nav
    const hideBottomNav = ['/mission/submit', '/mission/result', '/coupon/success'].includes(location.pathname);
    const isScanPage = location.pathname === '/scan';

    return (
        <div className="w-full h-full flex items-center justify-center bg-transparent">
            {/* The primary "phone" container */}
            <div className="relative w-full max-w-[420px] h-[100dvh] max-h-[850px] shadow-2xl rounded-[2.5rem] overflow-hidden flex flex-col sm:border-[8px] sm:border-slate-800/10 bg-white dark:bg-[#1a2322]">

                {/* Simulated status bar space if needed - hidden completely for full-screen immersive feel on specific pages */}
                {/* {!isScanPage && (
                    <div className="h-0 w-full shrink-0 flex items-center justify-center pointer-events-none sticky top-0 z-50">
                        <div className="w-1/3 h-[5px] bg-black/10 rounded-b-xl absolute top-0"></div>
                    </div>
                )} */}

                {/* Main Content Area */}
                <div className="flex-1 w-full h-full overflow-hidden relative">
                    <Outlet />
                </div>

                {/* Fixed Bottom Navigation (Only visible on main pages) */}
                {!hideBottomNav && (
                    <nav className="shrink-0 h-20 bg-white/80 dark:bg-[#1a2322]/80 backdrop-blur-xl border-t border-slate-200/50 dark:border-slate-800 flex justify-around items-center px-4 pb-4 pt-2 shadow-[0_-10px_40px_rgba(0,0,0,0.03)] z-40 sticky bottom-0">
                        {/* Nav Item: Home */}
                        <div
                            onClick={() => navigate('/')}
                            className={`flex flex-col items-center gap-1 cursor-pointer transition-all ${location.pathname === '/' ? 'text-[#37776f]' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}`}
                        >
                            <span className={`material-symbols-outlined text-2xl transition-transform ${location.pathname === '/' ? 'font-variation-settings-\'FILL\' 1; scale-110' : ''}`}>home</span>
                            <span className="text-[10px] font-bold tracking-wide">Home</span>
                        </div>

                        {/* Nav Item: Map (Placeholder action) */}
                        <div
                            onClick={() => { }}
                            className="flex flex-col items-center gap-1 cursor-pointer transition-all text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                            <span className="material-symbols-outlined text-2xl">map</span>
                            <span className="text-[10px] font-bold tracking-wide">Map</span>
                        </div>

                        {/* Nav Item: Wallet */}
                        <div
                            onClick={() => navigate('/wallet')}
                            className={`flex flex-col items-center gap-1 cursor-pointer transition-all ${location.pathname === '/wallet' ? 'text-[#37776f]' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}`}
                        >
                            <span className={`material-symbols-outlined text-2xl transition-transform ${location.pathname === '/wallet' ? 'font-variation-settings-\'FILL\' 1; scale-110' : ''}`}>account_balance_wallet</span>
                            <span className="text-[10px] font-bold tracking-wide">Wallet</span>
                        </div>

                        {/* Nav Item: Profile (Placeholder action) */}
                        <div
                            onClick={() => { }}
                            className="flex flex-col items-center gap-1 cursor-pointer transition-all text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                            <span className="material-symbols-outlined text-2xl">person</span>
                            <span className="text-[10px] font-bold tracking-wide">Profile</span>
                        </div>
                    </nav>
                )}

                {/* OS Bottom Home Bar Indicator (Simulated) */}
                <div className="h-1 w-full bg-transparent shrink-0 flex justify-center pb-2 pt-1 sticky bottom-0 z-50 pointer-events-none">
                    <div className="w-1/3 h-1 bg-black/20 dark:bg-white/20 rounded-full"></div>
                </div>

            </div>
        </div>
    );
}
