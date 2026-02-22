export default function CouponWallet() {
    return (
        <div className="font-display h-full w-full flex flex-col relative bg-gray-50 overflow-hidden antialiased">

            {/* Header / Summary Area */}
            <div className="bg-gradient-to-br from-coral-start to-coral-end pt-12 pb-8 px-6 text-white shrink-0 rounded-b-3xl shadow-sm z-10 relative">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-extrabold tracking-tight drop-shadow-sm">My Wallet</h1>
                    <button className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center hover:bg-white/30 transition-colors">
                        <span className="material-symbols-outlined text-white">notifications</span>
                    </button>
                </div>

                <div className="flex items-center gap-4 bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 shadow-inner">
                    <div className="w-12 h-12 rounded-full bg-white/30 flex items-center justify-center text-2xl font-bold shadow-sm">
                        P
                    </div>
                    <div>
                        <p className="text-xs text-white/90 font-medium tracking-wide">Total Rewards</p>
                        <p className="text-xl font-bold">12 Coupons</p>
                    </div>
                </div>
            </div>

            {/* Coupon List Area */}
            <div className="flex-1 overflow-y-auto no-scrollbar px-6 py-6 space-y-4 bg-gray-50 relative z-0 pb-28">

                <div className="flex justify-between items-center mb-2 px-1">
                    <h2 className="text-sm font-bold text-gray-500 uppercase tracking-widest">Available Coupons</h2>
                    <span className="text-xs font-semibold text-coral-end bg-coral-start/10 px-2 py-1 rounded-md">Recent First</span>
                </div>

                {/* Coupon Card 1 */}
                <div className="bg-white rounded-2xl p-4 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] flex items-center gap-4 border border-gray-100 transition-transform active:scale-[0.98] cursor-pointer hover:shadow-lg hover:border-coral-start/30">
                    <div className="w-16 h-16 rounded-xl bg-orange-50 flex-shrink-0 flex items-center justify-center border border-orange-100 overflow-hidden shadow-inner">
                        <img alt="Store logo" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDpNcQFwEXAAMmAgyvpncFuFrxLzxIx5OkHQqi6QsNoJWbteQapkyHrQn1MsKNdiJOrb9RxFVDVD4TZLh5IJaCE0FRdF1dlBaspITsZRKpYfnOI3IAmMUW7kbzR84cVDNbvIfEua9SfMj01Uw68wZQFCp3d22U6MNriwNzcsGhWlKY270xllmdiKfNdmMhB7q6FVqFaTSqx5dKrfSZDQuX69AAGZ2i8ZeidXKhr-LS6qKWqajWrJLCnAbunvKW5XlnADcCMOK-tWz4" />
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-gray-900 text-[15px] mb-0.5">Forest of Wisdom</h3>
                        <p className="text-coral-end font-extrabold text-lg leading-tight">10% OFF</p>
                        <p className="text-[10px] text-gray-400 font-medium mt-1">Expires Dec 31, 2026</p>
                    </div>
                    <div className="w-12 h-12 flex-shrink-0 bg-gray-50 rounded-lg p-1 border border-gray-100 shadow-inner flex items-center justify-center">
                        <span className="material-symbols-outlined text-gray-300 text-[28px]">qr_code_2</span>
                    </div>
                </div>

                {/* Coupon Card 2 */}
                <div className="bg-white rounded-2xl p-4 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] flex items-center gap-4 border border-gray-100 transition-transform active:scale-[0.98] cursor-pointer hover:shadow-lg hover:border-blue-300">
                    <div className="w-16 h-16 rounded-xl bg-blue-50 flex-shrink-0 flex items-center justify-center border border-blue-100 overflow-hidden shadow-inner">
                        <span className="material-symbols-outlined text-blue-400 text-3xl">auto_stories</span>
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-gray-900 text-[15px] mb-0.5">Book City Cafe</h3>
                        <p className="text-coral-end font-extrabold text-lg leading-tight">Free Americano</p>
                        <p className="text-[10px] text-gray-400 font-medium mt-1">Expires Jan 15, 2027</p>
                    </div>
                    <div className="w-12 h-12 flex-shrink-0 bg-gray-50 rounded-lg p-1 border border-gray-100 shadow-inner flex items-center justify-center">
                        <span className="material-symbols-outlined text-gray-300 text-[28px]">qr_code_2</span>
                    </div>
                </div>

                {/* Coupon Card 3 (Used/Expired visually) */}
                <div className="bg-white rounded-2xl p-4 shadow-sm flex items-center gap-4 border border-gray-100 transition-transform active:scale-[0.98] cursor-pointer opacity-70 grayscale-[20%]">
                    <div className="w-16 h-16 rounded-xl bg-purple-50 flex-shrink-0 flex items-center justify-center border border-purple-100 overflow-hidden shadow-inner">
                        <span className="material-symbols-outlined text-purple-400 text-3xl">museum</span>
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-gray-900 text-[15px] mb-0.5">Art Hall Paju</h3>
                        <p className="text-gray-500 font-extrabold text-lg leading-tight">BOGO Ticket</p>
                        <p className="text-[10px] text-gray-400 font-medium mt-1">Expired Dec 25, 2025</p>
                    </div>
                    <div className="w-12 h-12 flex-shrink-0 bg-gray-50 rounded-lg p-1 border border-gray-100 shadow-inner flex items-center justify-center">
                        <span className="material-symbols-outlined text-gray-200 text-[28px]">qr_code_2</span>
                    </div>
                </div>

                {/* Coupon Card 4 */}
                <div className="bg-white rounded-2xl p-4 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] flex items-center gap-4 border border-gray-100 transition-transform active:scale-[0.98] cursor-pointer hover:shadow-lg hover:border-green-300">
                    <div className="w-16 h-16 rounded-xl bg-green-50 flex-shrink-0 flex items-center justify-center border border-green-100 overflow-hidden shadow-inner">
                        <span className="material-symbols-outlined text-green-400 text-3xl">park</span>
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-gray-900 text-[15px] mb-0.5">Paju Nature Trail</h3>
                        <p className="text-coral-end font-extrabold text-lg leading-tight">Gift Set</p>
                        <p className="text-[10px] text-gray-400 font-medium mt-1">Expires Feb 01, 2027</p>
                    </div>
                    <div className="w-12 h-12 flex-shrink-0 bg-gray-50 rounded-lg p-1 border border-gray-100 shadow-inner flex items-center justify-center">
                        <span className="material-symbols-outlined text-gray-300 text-[28px]">qr_code_2</span>
                    </div>
                </div>
            </div>

        </div>
    );
}
