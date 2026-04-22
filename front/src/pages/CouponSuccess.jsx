import React from "react";
import { useNavigate } from "react-router-dom";
import { useMissionStore } from "../store/useMissionStore";

// Confetti Particles Data
const CONFETTI = [
    { left: "10%", color: "bg-yellow-300", speed: "animate-confetti-slow", delay: "0s" },
    { left: "20%", color: "bg-white", speed: "animate-confetti-fast", delay: "1.5s" },
    { left: "35%", color: "bg-blue-300", speed: "animate-confetti-medium", delay: "0.5s" },
    { left: "50%", color: "bg-green-300", speed: "animate-confetti-slow", delay: "2s" },
    { left: "65%", color: "bg-yellow-300", speed: "animate-confetti-fast", delay: "1s" },
    { left: "80%", color: "bg-white", speed: "animate-confetti-medium", delay: "0.2s" },
    { left: "90%", color: "bg-purple-300", speed: "animate-confetti-slow", delay: "2.5s" },
    { left: "15%", color: "bg-pink-300", speed: "animate-confetti-fast", delay: "3s" },
    { left: "40%", color: "bg-white", speed: "animate-confetti-medium", delay: "3.5s" },
    { left: "70%", color: "bg-blue-200", speed: "animate-confetti-slow", delay: "4s" },
];

export default function CouponSuccess() {
    const navigate = useNavigate();
    const { coupon } = useMissionStore();

    return (
        <div className="font-display h-full w-full flex flex-col relative overflow-hidden bg-background-light dark:bg-background-dark antialiased">

            {/* Main Mobile Screen Area */}
            <div className="relative w-full h-full bg-gradient-to-br from-[#f45c25] via-[#ff7e4f] to-[#e04812] flex flex-col overflow-hidden z-10 shrink-0">

                {/* Confetti Overlay */}
                <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
                    {CONFETTI.map((p, i) => (
                        <div
                            key={i}
                            className={`absolute top-[-20px] w-[10px] h-[10px] ${p.color} ${p.speed}`}
                            style={{ left: p.left, animationDelay: p.delay }}
                        />
                    ))}
                </div>

                {/* Content Wrapper */}
                <div className="flex-1 flex flex-col p-6 relative z-20 overflow-y-auto no-scrollbar">

                    {/* Success Header */}
                    <div className="mt-8 mb-6 text-center animate-float">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm mb-4 border border-white/30 text-white shadow-lg">
                            <span className="material-symbols-outlined text-4xl">celebration</span>
                        </div>
                        <h1 className="text-white text-4xl font-black leading-tight tracking-tight drop-shadow-sm">
                            미션 완료!
                        </h1>
                        <p className="text-white/90 text-sm font-medium mt-2 leading-relaxed">
                            파주 출판단지에서<br />탐험 미션을 성공적으로 마쳤습니다.
                        </p>
                    </div>

                    {/* Coupon Card */}
                    <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-6 flex-shrink-0 mx-2 transform transition-all hover:scale-[1.02]">
                        {/* Card Header Image */}
                        <div
                            className="h-32 w-full bg-cover bg-center relative"
                            style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDpNcQFwEXAAMmAgyvpncFuFrxLzxIx5OkHQqi6QsNoJWbteQapkyHrQn1MsKNdiJOrb9RxFVDVD4TZLh5IJaCE0FRdF1dlBaspITsZRKpYfnOI3IAmMUW7kbzR84cVDNbvIfEua9SfMj01Uw68wZQFCp3d22U6MNriwNzcsGhWlKY270xllmdiKfNdmMhB7q6FVqFaTSqx5dKrfSZDQuX69AAGZ2i8ZeidXKhr-LS6qKWqajWrJLCnAbunvKW5XlnADcCMOK-tWz4')" }}
                        >
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center overflow-hidden shadow-sm">
                                        <span className="material-symbols-outlined text-gray-800 text-sm">storefront</span>
                                    </div>
                                    <span className="text-white font-bold text-sm text-[shadow:0_1px_2px_rgba(0,0,0,0.5)]">지혜의 숲</span>
                                </div>
                            </div>
                        </div>

                        {/* Ticket Content */}
                        <div className="p-5 flex flex-col items-center text-center relative">
                            {/* Dashed Divider Simulation */}
                            <div className="absolute top-0 left-0 w-full transform -translate-y-1/2 flex justify-between px-2">
                                <div className="w-4 h-4 rounded-full bg-[#f45c25] dark:bg-[#e04812]"></div>
                                <div className="w-full border-t-2 border-dashed border-gray-300 mx-2 mt-2"></div>
                                <div className="w-4 h-4 rounded-full bg-[#f45c25] dark:bg-[#e04812]"></div>
                            </div>

                            <h2 className="text-gray-900 text-2xl font-black tracking-tight mb-1">{coupon?.discount_rule || '10% 할인'}</h2>
                            <p className="text-gray-500 text-xs uppercase tracking-wide font-semibold mb-6">{coupon?.answer || '미션 완료'} 보상 쿠폰</p>

                            {/* QR Code Block */}
                            <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 mb-4 shadow-inner">
                                <img
                                    alt="QR Code for redemption"
                                    className="w-32 h-32 mix-blend-multiply opacity-90"
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuDDBQRaA927Rd_zmaD1YfH7exFF0vRNU_J4ynRYy19zlIeWi9-UPVBTbFo8ZH3zgtByuR-JFMnl-JNvuZPqlR3ED3kSfCj6dvYkg1WF6KJz5Cdp87huC8NiXLGmJCw6qIddqciDwjrtkWjFKQrnKfYE9s9A6u6bbrrGp_Be9MDJDmL-6zrh0O6BYZy6VIq2pyQRVd7eHQa4ACZmdBCyMqIxFus6Hs3jxlHcXdLJuyBFGVToh1IrgXpdUGvk6WhzIz-sapxhk9yvD98"
                                />
                            </div>

                            <p className="text-gray-400 text-[10px]">매장 카운터에서 스캔하여 사용하세요</p>
                            <p className="text-[#f45c25] text-xs font-semibold mt-1">
                                만료일: {coupon ? new Date(coupon.expires_at).toLocaleDateString() : '2026. 12. 31.'}
                            </p>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-auto flex flex-col gap-3 pb-6">
                        <button
                            onClick={() => navigate('/scan')}
                            className="flex w-full cursor-pointer items-center justify-center rounded-xl h-14 px-6 bg-white text-[#f45c25] hover:bg-gray-50 transition-colors shadow-lg group"
                        >
                            <span className="text-base font-bold mr-2 group-hover:scale-105 transition-transform">지금 사용하기</span>
                            <span className="material-symbols-outlined text-xl group-hover:translate-x-1 transition-transform">arrow_forward</span>
                        </button>
                        <button
                            onClick={() => navigate('/wallet')}
                            className="flex w-full cursor-pointer items-center justify-center rounded-xl h-14 px-6 bg-transparent border-2 border-white/40 text-white hover:bg-white/10 hover:border-white transition-all backdrop-blur-sm group"
                        >
                            <span className="material-symbols-outlined mr-2 group-hover:rotate-12 transition-transform">account_balance_wallet</span>
                            <span className="text-base font-bold">지갑에 저장하기</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
