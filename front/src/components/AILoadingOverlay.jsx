import React, { useState, useEffect } from 'react';

const MESSAGES = [
    { title: "Analyzing Image...", desc: "Checking image quality and architectural features." },
    { title: "AI Verification...", desc: "Measuring confidence score against database." },
    { title: "Generating Result...", desc: "Finalizing your mission results." }
];

export default function AILoadingOverlay({ isVisible }) {
    const [step, setStep] = useState(0);

    useEffect(() => {
        if (!isVisible) {
            setStep(0);
            return;
        }

        const interval = setInterval(() => {
            setStep((prev) => Math.min(prev + 1, MESSAGES.length - 1));
        }, 3000); // Change message every 3 seconds

        return () => clearInterval(interval);
    }, [isVisible]);

    if (!isVisible) return null;

    const currentMsg = MESSAGES[step];

    return (
        <div className="absolute inset-0 z-[60] bg-slate-900/90 backdrop-blur-sm flex flex-col items-center justify-center p-8 transition-opacity duration-500">
            <div className="relative size-24 mb-8 flex items-center justify-center">
                {/* Glowing effect */}
                <div className="absolute inset-0 bg-primary/30 rounded-full blur-xl animate-pulse"></div>
                {/* Spinning Loader */}
                <svg className="animate-spin w-full h-full text-accent-peach" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {/* Logo Center */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="material-symbols-outlined text-white text-3xl">grid_view</span>
                </div>
            </div>
            <h3 className="text-white text-xl font-bold mb-2 animate-fade-in-up">{currentMsg.title}</h3>
            <p className="text-slate-400 text-sm text-center animate-fade-in-up">{currentMsg.desc}</p>
        </div>
    );
}
