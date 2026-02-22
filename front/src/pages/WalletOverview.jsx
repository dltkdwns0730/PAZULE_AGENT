import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function WalletOverview() {
    const navigate = useNavigate();
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedCoupon, setSelectedCoupon] = useState(null);

    const coupons = [
        {
            icon: "coffee",
            name: "Starbucks",
            discount: "10% Discount",
            expiry: "Valid until Oct 30, 2023",
            dDay: "D-5",
            blurPos: "-top-10 -right-10",
            gradient: "from-[#377770] to-[#2a5c56]", // Primary Gradient
            code: "STAR-10-OFF"
        },
        {
            icon: "restaurant",
            name: "Outback Steakhouse",
            discount: "Free Appetizer",
            expiry: "Valid until Nov 12, 2023",
            dDay: "D-12",
            blurPos: "-bottom-10 -left-10",
            gradient: "from-[#ffaf87] to-[#ff8e72]", // Accent Gradient
            code: "OUT-FREE-APP"
        },
        {
            icon: "attractions",
            name: "Lotte World",
            discount: "50% Off Entry",
            expiry: "Valid until Dec 01, 2023",
            dDay: "D-32",
            blurPos: null,
            gradient: "from-blue-500 to-blue-700",
            code: "LOTTE-50-ENT"
        },
    ];

    const openModal = (coupon) => {
        setSelectedCoupon(coupon);
        setModalOpen(true);
    };

    return (
        <div className="flex flex-col min-h-full bg-background-light dark:bg-background-dark text-gray-900 dark:text-white pb-24">
            <style>{`
                .no-scrollbar::-webkit-scrollbar { display: none; }
                .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
            `}</style>

            {/* Header */}
            <header className="flex items-center justify-between px-6 py-5 bg-white/90 dark:bg-[#1e2827]/90 backdrop-blur-md z-10 sticky top-0 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 -ml-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200 transition-colors"
                    >
                        <span className="material-symbols-outlined">arrow_back</span>
                    </button>
                    <h2 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">My Wallet</h2>
                </div>
                <button className="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200 transition-colors">
                    <span className="material-symbols-outlined">notifications</span>
                    <span className="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-[#1e2827]"></span>
                </button>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto no-scrollbar px-6 pt-6">
                <div className="flex flex-col gap-1 mb-6">
                    <h1 className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">My Coupons</h1>
                    <div className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center bg-primary/10 text-primary text-xs font-bold px-2.5 py-1 rounded-full">
                            {coupons.length} Active
                        </span>
                        <span className="text-gray-400 text-sm font-medium">Updated just now</span>
                    </div>
                </div>

                {/* Coupon cards grid */}
                <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
                    {coupons.map((c, i) => (
                        <div
                            key={i}
                            className="block transform transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                            onClick={() => openModal(c)}
                        >
                            <div className={`relative w-full aspect-[1.8/1] bg-gradient-to-br ${c.gradient} rounded-2xl p-6 shadow-lg flex flex-col justify-between overflow-hidden group`}>
                                {/* Decorative Blur */}
                                {c.blurPos && (
                                    <div className={`absolute ${c.blurPos} w-32 h-32 bg-white/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500`}></div>
                                )}

                                <div className="relative z-10 flex justify-between items-start">
                                    <div className="w-12 h-12 bg-white/90 dark:bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm text-gray-800 dark:text-white">
                                        <span className="material-symbols-outlined text-[24px]">{c.icon}</span>
                                    </div>
                                    <span className="bg-black/20 backdrop-blur-md text-white border border-white/10 text-xs font-semibold px-2 py-1 rounded-lg">
                                        {c.dDay}
                                    </span>
                                </div>
                                <div className="relative z-10">
                                    <p className="text-white text-2xl font-bold leading-tight mb-1 drop-shadow-sm">{c.discount}</p>
                                    <p className="text-white/90 font-bold text-sm tracking-wide uppercase opacity-90">
                                        {c.name}
                                    </p>
                                    <p className="text-white/70 text-xs mt-3 font-medium bg-black/10 inline-block px-2 py-0.5 rounded backdrop-blur-sm">{c.expiry}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </main>

            {/* Modal */}
            {modalOpen && selectedCoupon && (
                <div className="fixed inset-0 z-50 flex flex-col justify-end isolate">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                        onClick={() => setModalOpen(false)}
                    ></div>

                    {/* Modal Content */}
                    <div className="relative z-10 bg-white dark:bg-[#1e2827] w-full max-w-[640px] mx-auto rounded-t-[2rem] p-6 pb-10 animate-slide-up shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.3)] lg:max-w-[430px] border-t border-white/10">
                        <div className="w-12 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full mx-auto mb-6"></div>
                        <div className="text-center mb-6">
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{selectedCoupon.name}</h3>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">{selectedCoupon.discount}</p>
                        </div>
                        <div className="flex flex-col items-center justify-center mb-8">
                            <div className="p-4 border-2 border-dashed border-primary/30 rounded-2xl bg-primary/5 mb-4 relative overflow-hidden">
                                <img
                                    alt="QR Code"
                                    className="w-48 h-48 mix-blend-multiply dark:mix-blend-normal dark:invert brightness-90 dark:brightness-100"
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuAyokZTAY8nALlysdMinaShdGeR39nfeylQlYeoqSwV88fGyXj-dG1BWGlzSIoShoSQkgAwFKF3_gG13vAhmwVF0vTutiSxgZr38--OK2kL5f8oY41rN6V7qqxDn8Iw1h-9PUuaz6SHMFmm3qdxZTxVBdpB1EKKPnR2BTRGoFuQ03mPll6aXwrnrT4DLr-JfppYF2Nm_ljtx7-fwzQfj9kTsP7GPFtCidWi11fB8Zb4hZNuxG5yGw3QZb66-gy9RxQwsGvFOZczE8s"
                                />
                                {/* Scan Line Animation */}
                                <div className="absolute top-0 left-0 right-0 h-1 bg-primary/50 blur-[2px] animate-[scan_2s_ease-in-out_infinite]"></div>
                            </div>
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Show this code to the cashier</p>
                            <p className="text-lg font-mono font-bold text-gray-900 dark:text-white tracking-widest">{selectedCoupon.code}</p>

                            <div className="flex items-center gap-2 text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-1.5 rounded-lg mt-4">
                                <span className="material-symbols-outlined text-[18px]">timer</span>
                                <span className="text-sm font-bold font-mono">04:59</span>
                            </div>
                        </div>
                        <button
                            className="w-full flex items-center justify-center py-4 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-white font-bold text-base hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                            onClick={() => setModalOpen(false)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
