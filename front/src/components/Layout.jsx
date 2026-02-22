import { Outlet, NavLink, useLocation } from "react-router-dom";

export default function Layout() {
    const location = useLocation();

    return (
        <div className="min-h-screen bg-[#111111] lg:flex lg:items-center lg:justify-center lg:py-8 font-display">
            {/* Phone Frame Container */}
            <div className="
                w-full min-h-screen flex flex-col relative overflow-hidden
                md:max-w-[640px] md:mx-auto
                lg:max-w-[400px] lg:min-h-0 lg:h-[850px] lg:rounded-[2.5rem] lg:shadow-2xl lg:shadow-black/50 
                lg:border-[8px] lg:border-[#2a3534] lg:ring-1 lg:ring-black/5
            ">
                {/* Status Bar (Simulated) */}
                <div className="h-10 w-full bg-white dark:bg-[#1e2827] flex items-center justify-between px-6 select-none shrink-0 z-50 transition-colors">
                    <span className="text-xs font-bold text-gray-900 dark:text-white">9:41</span>
                    <div className="flex gap-1.5">
                        <span className="material-symbols-outlined text-[16px] text-gray-900 dark:text-white">signal_cellular_alt</span>
                        <span className="material-symbols-outlined text-[16px] text-gray-900 dark:text-white">wifi</span>
                        <span className="material-symbols-outlined text-[16px] text-gray-900 dark:text-white">battery_full</span>
                    </div>
                </div>

                {/* Content Area */}
                <main className="flex-1 overflow-y-auto overflow-x-hidden bg-background-light dark:bg-background-dark no-scrollbar pb-24">
                    <Outlet />
                </main>

                {/* Bottom Navigation */}
                <nav className="
                    absolute bottom-0 w-full
                    bg-white/90 dark:bg-[#1e2827]/90 backdrop-blur-md border-t border-gray-200 dark:border-gray-800
                    pb-5 pt-3 px-6 z-40
                ">
                    <div className="flex justify-between items-center px-4">
                        <NavLink to="/" end className={({ isActive }) => `flex flex-col items-center gap-1 group w-14 ${isActive ? "text-primary" : "text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"}`}>
                            <div className="relative">
                                <span className="material-symbols-outlined text-[26px] group-hover:scale-110 transition-transform">home</span>
                                {location.pathname === '/' && <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary rounded-full"></span>}
                            </div>
                            <span className="text-[10px] font-bold">Home</span>
                        </NavLink>

                        <NavLink to="/map" className={({ isActive }) => `flex flex-col items-center gap-1 group w-14 ${isActive ? "text-primary" : "text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"}`}>
                            <span className="material-symbols-outlined text-[26px] group-hover:scale-110 transition-transform">map</span>
                            <span className="text-[10px] font-medium">Map</span>
                        </NavLink>

                        <NavLink to="/wallet" className={({ isActive }) => `flex flex-col items-center gap-1 group w-14 ${isActive ? "text-primary" : "text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"}`}>
                            <span className="material-symbols-outlined text-[26px] group-hover:scale-110 transition-transform">account_balance_wallet</span>
                            <span className="text-[10px] font-medium">Wallet</span>
                        </NavLink>

                        <NavLink to="/profile" className={({ isActive }) => `flex flex-col items-center gap-1 group w-14 ${isActive ? "text-primary" : "text-gray-400 dark:text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"}`}>
                            <div className="relative">
                                <span className="material-symbols-outlined text-[26px] group-hover:scale-110 transition-transform">person</span>
                                <span className="absolute top-0 right-0 w-2 h-2 bg-accent rounded-full border border-white dark:border-[#1e2827]"></span>
                            </div>
                            <span className="text-[10px] font-medium">Profile</span>
                        </NavLink>
                    </div>
                </nav>

                {/* Home Indicator (iOS style) */}
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-32 h-1 bg-gray-300 dark:bg-gray-600 rounded-full z-50"></div>
            </div>
        </div>
    );
}
