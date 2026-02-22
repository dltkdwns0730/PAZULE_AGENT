import { useNavigate } from "react-router-dom";

export default function Onboarding() {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col h-full bg-primary font-display relative overflow-hidden text-white">
            {/* Background Decoration */}
            <div className="absolute top-[-20%] right-[-20%] w-[80%] aspect-square bg-accent/20 rounded-full blur-3xl"></div>
            <div className="absolute bottom-[-10%] left-[-10%] w-[60%] aspect-square bg-white/10 rounded-full blur-3xl"></div>

            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center relative z-10">
                {/* Icon/Illustration */}
                <div className="w-32 h-32 bg-white/10 backdrop-blur-md rounded-[2rem] flex items-center justify-center mb-10 shadow-glow animate-float">
                    <span className="material-symbols-outlined text-[64px] text-white">explore</span>
                </div>

                <h1 className="text-4xl font-black mb-4 tracking-tight leading-tight">
                    Discover <br />
                    <span className="text-accent">Hidden Paju</span>
                </h1>

                <p className="text-white/80 text-lg leading-relaxed max-w-[280px] mx-auto mb-12">
                    Explore the Book City, find secret spots, and earn exclusive rewards.
                </p>

                {/* Pagination Dots (Static for now) */}
                <div className="flex gap-2 mb-12">
                    <div className="w-8 h-2 bg-white rounded-full"></div>
                    <div className="w-2 h-2 bg-white/30 rounded-full"></div>
                    <div className="w-2 h-2 bg-white/30 rounded-full"></div>
                </div>
            </div>

            {/* Bottom Section */}
            <div className="p-8 pb-12 bg-black/10 backdrop-blur-sm border-t border-white/10">
                <button
                    onClick={() => navigate('/permissions')}
                    className="w-full h-14 bg-white text-primary rounded-xl shadow-lg flex items-center justify-center gap-2 font-bold text-lg hover:bg-gray-100 active:scale-[0.98] transition-all"
                >
                    Get Started
                    <span className="material-symbols-outlined">arrow_forward</span>
                </button>
                <div className="mt-4 text-center">
                    <span className="text-white/60 text-xs text-center">Already have an account? <button className="text-white font-bold hover:underline">Log In</button></span>
                </div>
            </div>
        </div>
    );
}
