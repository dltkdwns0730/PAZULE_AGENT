import React, { useState, useEffect } from "react";

const LOADING_MESSAGES = [
    "Analyzing architectural features...",
    "Matching with reference context...",
    "Cross-referencing angles...",
    "Verifying location...",
    "Almost there..."
];

export default function AILoadingOverlay({ isVisible }) {
    const [messageIndex, setMessageIndex] = useState(0);

    // Cycle through messages while visible
    useEffect(() => {
        let interval;
        if (isVisible) {
            setMessageIndex(0); // Reset when becoming visible
            interval = setInterval(() => {
                setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
            }, 2500); // Change message every 2.5 seconds
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isVisible]);

    if (!isVisible) return null;

    return (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-black/80 backdrop-blur-md transition-all duration-300">
            <div className="flex flex-col items-center justify-center p-8 text-center max-w-[300px] bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl border border-slate-100 dark:border-slate-800">
                
                {/* Central Animation */}
                <div className="relative w-24 h-24 mb-6">
                    {/* Outer glowing rings */}
                    <div className="absolute inset-0 rounded-full border-[3px] border-primary/20 animate-[spin_3s_linear_infinite]"></div>
                    <div className="absolute inset-2 rounded-full border-[3px] border-accent-orange/30 border-t-accent-orange animate-[spin_2s_linear_infinite_reverse]"></div>
                    
                    {/* Inner core */}
                    <div className="absolute inset-4 bg-gradient-to-br from-primary to-primary-dark rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(55,119,111,0.4)] animate-pulse">
                        <span className="material-symbols-outlined text-white text-[32px] font-variation-settings-'FILL' 1;">psychology</span>
                    </div>
                    
                    {/* Scanning line effect */}
                    <div className="absolute top-0 left-0 w-full h-[2px] bg-white/60 shadow-[0_0_10px_2px_rgba(255,255,255,0.8)] animate-[scan_2s_ease-in-out_infinite]"></div>
                </div>

                <h3 className="text-xl font-extrabold text-slate-800 dark:text-white mb-2 font-display tracking-tight">AI Vision Engine</h3>
                
                <div className="h-[40px] flex items-center justify-center">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400 leading-snug animate-fade-in-up key={messageIndex}">
                        {LOADING_MESSAGES[messageIndex]}
                    </p>
                </div>

                {/* Progress bar simulation */}
                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mt-6">
                    <div className="h-full bg-gradient-to-r from-primary to-accent-mint w-full rounded-full animate-[slideRight_2s_ease-in-out_infinite] origin-left scale-x-50"></div>
                </div>
            </div>
            
            <style jsx>{`
                @keyframes slideRight {
                    0% { transform: translateX(-100%); }
                    50% { transform: translateX(0); }
                    100% { transform: translateX(100%); }
                }
            `}</style>
        </div>
    );
}
