export default function AdminDashboard() {
    return (
        <div className="flex min-h-screen w-full overflow-hidden bg-background-light dark:bg-background-dark text-slate-900 dark:text-white font-display">
            <aside className="w-64 bg-admin-primary flex-shrink-0 flex flex-col justify-between hidden md:flex h-screen fixed left-0 top-0 z-50 text-white">
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-10">
                        <div className="flex items-center justify-center bg-white/10 rounded-lg h-10 w-10">
                            <span className="material-symbols-outlined text-white">grid_view</span>
                        </div>
                        <div className="flex flex-col">
                            <h1 className="text-white text-lg font-bold leading-none tracking-tight">PAZULE</h1>
                            <p className="text-white/60 text-xs font-normal mt-1">Admin Control</p>
                        </div>
                    </div>
                    <nav className="flex flex-col gap-2">
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/10 text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">dashboard</span>
                            <span className="text-sm font-medium">Dashboard</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">monitoring</span>
                            <span className="text-sm font-medium">Live Monitor</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">confirmation_number</span>
                            <span className="text-sm font-medium">Coupon Management</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">psychology</span>
                            <span className="text-sm font-medium">AI Configuration</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">group</span>
                            <span className="text-sm font-medium">Users</span>
                        </a>
                    </nav>
                </div>
                <div className="p-6">
                    <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                        <span className="material-symbols-outlined">settings</span>
                        <span className="text-sm font-medium">Settings</span>
                    </a>
                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-3 px-2">
                        <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDJ00lxcOUtxA6QxKJapEvzZ2Be0fVETyx65raeNnDXwV64dS7fa4bg5GwLegn68FP8u9o0hRHtzLR_lruitHbEdFb5OstTilgQcsfO0vN7jtrCfrm4dxbuNbAz_brTaaFXgrqhIUlqq-p34KmadvonvT01801ctEg9sXORyuxRB-GljRJV_72vzzLyUrRi6FndP9mTEu-TeGAQzC6r0PuMnq0ggrM8TEB0Cz7xBzFTjk3uYrRjhMPApI-EJN8RRmcDuXISpeeqW38')" }}></div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium text-white">Admin User</span>
                            <span className="text-xs text-white/50">admin@pazule.io</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="flex-1 md:ml-64 flex flex-col h-screen overflow-y-auto">
                <header className="bg-white dark:bg-[#1e2625] border-b border-admin-neutral-light dark:border-white/5 sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button className="md:hidden text-slate-500">
                            <span className="material-symbols-outlined">menu</span>
                        </button>
                        <h2 className="text-slate-900 dark:text-white text-xl font-bold tracking-tight">Dashboard Overview</h2>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="hidden sm:flex items-center bg-admin-neutral-light dark:bg-white/5 rounded-lg px-3 py-2 w-64">
                            <span className="material-symbols-outlined text-slate-400 dark:text-slate-500 text-[20px]">search</span>
                            <input className="bg-transparent border-none outline-none text-sm ml-2 w-full text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:ring-0 p-0" placeholder="Search logs, IDs, users..." type="text" />
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="relative p-2 text-slate-500 hover:text-admin-primary transition-colors rounded-full hover:bg-admin-neutral-light dark:hover:bg-white/5">
                                <span className="material-symbols-outlined">notifications</span>
                                <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 border-2 border-white dark:border-[#1e2625]"></span>
                            </button>
                            <button className="p-2 text-slate-500 hover:text-admin-primary transition-colors rounded-full hover:bg-admin-neutral-light dark:hover:bg-white/5">
                                <span className="material-symbols-outlined">calendar_today</span>
                            </button>
                        </div>
                    </div>
                </header>

                <div className="p-6 md:p-8 space-y-8 max-w-[1600px] mx-auto w-full">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white dark:bg-[#1e2625] rounded-xl p-6 shadow-sm border border-admin-neutral-light dark:border-white/5 relative overflow-hidden group">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Total Sessions</p>
                                    <h3 className="text-3xl font-bold text-slate-900 dark:text-white">14,203</h3>
                                </div>
                                <div className="bg-admin-primary/10 p-2 rounded-lg text-admin-primary">
                                    <span className="material-symbols-outlined">bar_chart</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[14px]">trending_up</span> 12%
                                </span>
                                <span className="text-slate-400 text-sm">vs last month</span>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1e2625] rounded-xl p-6 shadow-sm border border-admin-neutral-light dark:border-white/5 relative overflow-hidden group">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Success Rate</p>
                                    <h3 className="text-3xl font-bold text-slate-900 dark:text-white">94.2%</h3>
                                </div>
                                <div className="bg-admin-secondary/20 p-2 rounded-lg text-admin-primary">
                                    <span className="material-symbols-outlined">check_circle</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-admin-secondary font-semibold text-sm">+2.4%</span>
                                <span className="text-slate-400 text-sm">improvement</span>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1e2625] rounded-xl p-6 shadow-sm border border-admin-neutral-light dark:border-white/5 relative overflow-hidden group">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Coupons Issued</p>
                                    <h3 className="text-3xl font-bold text-slate-900 dark:text-white">8,500</h3>
                                </div>
                                <div className="bg-purple-100 dark:bg-purple-900/30 p-2 rounded-lg text-purple-600 dark:text-purple-400">
                                    <span className="material-symbols-outlined">local_activity</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[14px]">trending_up</span> 5.1%
                                </span>
                                <span className="text-slate-400 text-sm">vs last month</span>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                        <div className="xl:col-span-2 flex flex-col gap-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    <span className="material-symbols-outlined text-admin-primary">rss_feed</span>
                                    Mission Live Log
                                </h3>
                                <div className="flex gap-2">
                                    <button className="text-xs font-medium bg-white dark:bg-[#1e2625] border border-admin-neutral-light dark:border-white/10 text-slate-600 dark:text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">Export CSV</button>
                                    <button className="text-xs font-medium bg-white dark:bg-[#1e2625] border border-admin-neutral-light dark:border-white/10 text-slate-600 dark:text-slate-300 px-3 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">Filter</button>
                                </div>
                            </div>
                            <div className="bg-white dark:bg-[#1e2625] border border-admin-neutral-light dark:border-white/5 rounded-xl overflow-hidden shadow-sm">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-slate-50 dark:bg-white/5 border-b border-admin-neutral-light dark:border-white/5 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                                                <th className="px-6 py-4 font-semibold">Mission ID</th>
                                                <th className="px-6 py-4 font-semibold">User</th>
                                                <th className="px-6 py-4 font-semibold">Type</th>
                                                <th className="px-6 py-4 font-semibold">AI Confidence</th>
                                                <th className="px-6 py-4 font-semibold">Status</th>
                                                <th className="px-6 py-4 font-semibold text-right">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-admin-neutral-light dark:divide-white/5">
                                            <tr className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group cursor-pointer" onClick={() => window.location.href = '/admin/log'}>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-slate-900 dark:text-white">#M-9281</span>
                                                        <span className="text-xs text-slate-400">2 mins ago</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-8 w-8 rounded-full bg-slate-200 bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCIuGEDg0a8orCRbpB5oll6Ih4D_Usuj1xiuGMJ-hS7cdkU0ckEso_jR1nE5UGnM6Dcr57_f0mPGru1UOr285-9QQgx7lwhHrBLDOEu8MlCRIA5o842kYeBNfYA_fJntsl654ZHQAzw233Xm5sx-2T8TCviJVqVb8ye9cdY5Ved_N31pMuZsTvNfpdc0rZygHQpwblSUFrUBHbVTwi56wUkXeTS2FwOW0fWh5n3zcpCjdSWYxIYEiQV8IiEkWq-zFEHCsVtEnQwzrc')" }}></div>
                                                        <span className="text-sm text-slate-700 dark:text-slate-200">Alice Freeman</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">Location</span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex-1 w-24 bg-admin-neutral-light dark:bg-white/10 rounded-full h-1.5 overflow-hidden">
                                                            <div className="bg-admin-primary h-1.5 rounded-full" style={{ width: "98%" }}></div>
                                                        </div>
                                                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300">98%</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-admin-secondary/10 text-[#2a8c6e] border border-admin-secondary/20">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-admin-secondary mr-1.5"></span>
                                                        Approved
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <button className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                                                        <span className="material-symbols-outlined text-[20px]">more_vert</span>
                                                    </button>
                                                </td>
                                            </tr>
                                            {/* More rows would go here */}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div className="xl:col-span-1 flex flex-col gap-4">
                            <div className="flex items-center justify-between h-[36px]">
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    <span className="material-symbols-outlined text-admin-primary">auto_graph</span>
                                    Model Performance
                                </h3>
                                <button className="text-slate-400 hover:text-admin-primary">
                                    <span className="material-symbols-outlined">refresh</span>
                                </button>
                            </div>
                            <div className="bg-white dark:bg-[#1e2625] border border-admin-neutral-light dark:border-white/5 rounded-xl p-6 shadow-sm flex-1 flex flex-col justify-between min-h-[400px]">
                                <div className="mb-6">
                                    <p className="text-xs text-slate-500 uppercase font-semibold mb-4">Accuracy Comparison</p>
                                    <div className="space-y-5">
                                        <div>
                                            <div className="flex justify-between text-sm mb-1.5">
                                                <span className="font-medium text-slate-700 dark:text-slate-200">BLIP</span>
                                                <span className="font-bold text-slate-900 dark:text-white">82.4%</span>
                                            </div>
                                            <div className="w-full bg-admin-neutral-light dark:bg-white/10 rounded-full h-2.5 overflow-hidden">
                                                <div className="bg-admin-primary/50 h-2.5 rounded-full" style={{ width: "82.4%" }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-1.5">
                                                <span className="font-medium text-slate-700 dark:text-slate-200">CLIP</span>
                                                <span className="font-bold text-slate-900 dark:text-white">88.1%</span>
                                            </div>
                                            <div className="w-full bg-admin-neutral-light dark:bg-white/10 rounded-full h-2.5 overflow-hidden">
                                                <div className="bg-admin-primary/70 h-2.5 rounded-full" style={{ width: "88.1%" }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-1.5">
                                                <span className="font-medium text-slate-700 dark:text-slate-200">SigLIP2</span>
                                                <span className="font-bold text-slate-900 dark:text-white">96.5%</span>
                                            </div>
                                            <div className="w-full bg-admin-neutral-light dark:bg-white/10 rounded-full h-2.5 overflow-hidden">
                                                <div className="bg-admin-primary h-2.5 rounded-full shadow-[0_0_10px_rgba(55,119,112,0.4)]" style={{ width: "96.5%" }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-sm mb-1.5">
                                                <span className="font-medium text-slate-700 dark:text-slate-200">Qwen-VL</span>
                                                <span className="font-bold text-slate-900 dark:text-white">91.2%</span>
                                            </div>
                                            <div className="w-full bg-admin-neutral-light dark:bg-white/10 rounded-full h-2.5 overflow-hidden">
                                                <div className="bg-admin-primary/80 h-2.5 rounded-full" style={{ width: "91.2%" }}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="border-t border-admin-neutral-light dark:border-white/5 pt-6">
                                    <p className="text-xs text-slate-500 uppercase font-semibold mb-4">System Health</p>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 rounded-lg bg-admin-neutral-light dark:bg-white/5">
                                            <p className="text-xs text-slate-500 mb-1">Latency</p>
                                            <p className="text-lg font-bold text-slate-900 dark:text-white">42ms</p>
                                        </div>
                                        <div className="p-3 rounded-lg bg-admin-neutral-light dark:bg-white/5">
                                            <p className="text-xs text-slate-500 mb-1">Uptime</p>
                                            <p className="text-lg font-bold text-slate-900 dark:text-white">99.9%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
