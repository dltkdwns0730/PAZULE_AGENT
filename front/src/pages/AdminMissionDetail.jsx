export default function AdminMissionDetail() {
    return (
        <div className="flex min-h-screen w-full overflow-hidden bg-background-light dark:bg-background-dark text-slate-900 dark:text-white font-display">
            <aside className="w-64 bg-admin-primary flex-shrink-0 flex flex-col justify-between hidden md:flex h-screen fixed left-0 top-0 z-50 text-white">
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-10">
                        <div className="flex items-center justify-center bg-white/10 rounded-lg h-10 w-10">
                            <span className="material-symbols-outlined text-white text-[24px]">grid_view</span>
                        </div>
                        <div className="flex flex-col">
                            <h1 className="text-white text-lg font-bold leading-none tracking-tight">PAZULE</h1>
                            <p className="text-white/60 text-xs font-normal mt-1">Admin Control</p>
                        </div>
                    </div>
                    <nav className="flex flex-col gap-2">
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="/admin">
                            <span className="material-symbols-outlined">dashboard</span>
                            <span className="text-sm font-medium">Dashboard</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/10 text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">monitoring</span>
                            <span className="text-sm font-medium">Analysis Log</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">confirmation_number</span>
                            <span className="text-sm font-medium">Coupon Management</span>
                        </a>
                        <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/5 hover:text-white transition-colors" href="#">
                            <span className="material-symbols-outlined">psychology</span>
                            <span className="text-sm font-medium">AI Configuration</span>
                        </a>
                    </nav>
                </div>
                <div className="p-6">
                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-3 px-2">
                        <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDJ00lxcOUtxA6QxKJapEvzZ2Be0fVETyx65raeNnDXwV64dS7fa4bg5GwLegn68FP8u9o0hRHtzLR_lruitHbEdFb5OstTilgQcsfO0vN7jtrCfrm4dxbuNbAz_brTaaFXgrqhIUlqq-p34KmadvonvT01801ctEg9sXORyuxRB-GljRJV_72vzzLyUrRi6FndP9mTEu-TeGAQzC6r0PuMnq0ggrM8TEB0Cz7xBzFTjk3uYrRjhMPApI-EJN8RRmcDuXISpeeqW38')" }}></div>
                        <div className="flex flex-col overflow-hidden">
                            <span className="text-sm font-medium text-white truncate">Admin User</span>
                            <span className="text-xs text-white/50 truncate">admin@pazule.io</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="flex-1 md:ml-64 flex flex-col h-screen overflow-hidden">
                <header className="bg-white dark:bg-[#1e2625] border-b border-admin-neutral-light dark:border-white/5 sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button className="md:hidden text-slate-500">
                            <span className="material-symbols-outlined">menu</span>
                        </button>
                        <div className="flex items-center gap-2">
                            <a className="text-slate-400 hover:text-admin-primary transition-colors" href="/admin">
                                <span className="material-symbols-outlined text-[20px]">arrow_back</span>
                            </a>
                            <h2 className="text-slate-900 dark:text-white text-xl font-bold tracking-tight">AI Mission Detailed Analysis Log</h2>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-medium text-slate-400">
                        <span>SESSION ID: <span className="text-slate-900 dark:text-white">PZ-9281-X7</span></span>
                        <span className="h-4 w-px bg-slate-200 dark:bg-white/10"></span>
                        <span>2023-11-24 14:22:01 UTC</span>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 bg-background-light dark:bg-background-dark scrollbar-hide">
                    <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-12 gap-8">
                        <div className="xl:col-span-7 space-y-6">
                            <div className="bg-white dark:bg-[#1e2625] rounded-xl overflow-hidden shadow-sm border border-admin-neutral-light dark:border-white/5 relative group">
                                <div className="aspect-video relative bg-slate-100 dark:bg-admin-neutral-dark">
                                    <img alt="User Submission" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB9UeheTk9e6CLBJFWhAWbf8SNIqcQZQfzhn5UjD3OXSyoPkZz3XvymyD4BofAM1D8KtPmRwr8mEZKERGKKprYntwyW9Jd-1nsK3xqCOqesQxUqUw3aCSLYcjh8Ku2awN5zAGUdutoEaJ4Xf9DKR02FMMZFuCZ8r6gWFqig3pJlgK6527MiEeR3moxdgMAzf8eIM2hcld4BAw3CJ0W_GxvePNsOUoOGIx4_AyeMs4KA6qo5nM93I0yrMKngRKeNTS4cW-6iZ0uUMQA" />
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-6">
                                        <div className="bg-black/60 backdrop-blur-md rounded-lg p-4 text-white border border-white/10">
                                            <h4 className="text-xs font-bold uppercase tracking-widest text-admin-secondary mb-3">Metadata Analysis</h4>
                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div className="flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-[18px] text-white/60">location_on</span>
                                                    <div>
                                                        <p className="text-[10px] text-white/40 uppercase leading-none mb-1">GPS Coordinates</p>
                                                        <p className="font-mono text-xs">35.6895° N, 139.6917° E</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-[18px] text-admin-secondary">verified</span>
                                                    <div>
                                                        <p className="text-[10px] text-white/40 uppercase leading-none mb-1">Timestamp Validation</p>
                                                        <p className="text-xs font-semibold">MATCHED (± 2.4s)</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-4 border-t border-admin-neutral-light dark:border-white/5 flex justify-between items-center bg-slate-50 dark:bg-white/[0.02]">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-full border-2 border-white shadow-sm bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCIuGEDg0a8orCRbpB5oll6Ih4D_Usuj1xiuGMJ-hS7cdkU0ckEso_jR1nE5UGnM6Dcr57_f0mPGru1UOr285-9QQgx7lwhHrBLDOEu8MlCRIA5o842kYeBNfYA_fJntsl654ZHQAzw233Xm5sx-2T8TCviJVqVb8ye9cdY5Ved_N31pMuZsTvNfpdc0rZygHQpwblSUFrUBHbVTwi56wUkXeTS2FwOW0fWh5n3zcpCjdSWYxIYEiQV8IiEkWq-zFEHCsVtEnQwzrc')" }}></div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900 dark:text-white">Alice Freeman</p>
                                            <p className="text-xs text-slate-500">Mission: "Cozy Cafe Vibes"</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white dark:bg-[#1e2625] rounded-xl p-6 shadow-sm border border-admin-neutral-light dark:border-white/5">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-admin-primary text-[20px]">account_tree</span>
                                    System Trace: LangGraph Pipeline
                                </h3>
                                <div className="relative">
                                    <div className="absolute left-[15px] top-2 bottom-2 w-px bg-slate-200 dark:bg-white/10"></div>
                                    <div className="space-y-6">
                                        <div className="relative pl-10">
                                            <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-admin-primary flex items-center justify-center text-white z-10 shadow-sm">
                                                <span className="material-symbols-outlined text-[16px]">security</span>
                                            </div>
                                            <div>
                                                <div className="flex justify-between items-center mb-1">
                                                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Gatekeeper Node</h4>
                                                    <span className="text-[10px] font-mono text-slate-400">0.42ms</span>
                                                </div>
                                                <p className="text-xs text-slate-500">Validation passed. No NSFW content detected. Metadata integrity check: 100%.</p>
                                            </div>
                                        </div>
                                        <div className="relative pl-10">
                                            <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-admin-primary flex items-center justify-center text-white z-10 shadow-sm">
                                                <span className="material-symbols-outlined text-[16px]">alt_route</span>
                                            </div>
                                            <div>
                                                <div className="flex justify-between items-center mb-1">
                                                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Task Router</h4>
                                                    <span className="text-[10px] font-mono text-slate-400">1.2ms</span>
                                                </div>
                                                <p className="text-xs text-slate-500">Routing to Image-Text Consensus cluster. Mission type identified: <span className="text-admin-primary font-medium">Atmosphere_Visual</span>.</p>
                                            </div>
                                        </div>
                                        <div className="relative pl-10">
                                            <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-admin-secondary flex items-center justify-center text-white z-10 shadow-sm">
                                                <span className="material-symbols-outlined text-[16px]">call_split</span>
                                            </div>
                                            <div>
                                                <div className="flex justify-between items-center mb-1">
                                                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">Fan-out Parallel Process</h4>
                                                    <span className="text-[10px] font-mono text-slate-400">421ms</span>
                                                </div>
                                                <p className="text-xs text-slate-500">Initializing BLIP, CLIP, SigLIP2, and Qwen-VL vision encoders in parallel...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="xl:col-span-5 space-y-6">
                            <div className="bg-white dark:bg-[#1e2625] rounded-xl p-1 shadow-sm border border-admin-neutral-light dark:border-white/5 overflow-hidden">
                                <div className="bg-admin-secondary/10 dark:bg-admin-secondary/5 p-6 rounded-lg border border-admin-secondary/20">
                                    <div className="flex justify-between items-center mb-4">
                                        <span className="px-2.5 py-1 rounded bg-admin-secondary text-admin-primary font-bold text-xs uppercase tracking-widest">SUCCESS</span>
                                        <div className="text-right">
                                            <p className="text-[10px] text-slate-500 uppercase font-bold leading-none mb-1">Aggregate Confidence</p>
                                            <p className="text-2xl font-black text-slate-900 dark:text-white">94.8<span className="text-sm font-normal text-slate-400">%</span></p>
                                        </div>
                                    </div>
                                    <p className="text-sm text-slate-600 dark:text-slate-300">The ensemble models have reached a consensus. The submitted image accurately represents the mission criteria for <strong>"Cozy Cafe Vibes"</strong>.</p>
                                </div>
                            </div>

                            <div className="bg-white dark:bg-[#1e2625] rounded-xl p-6 shadow-sm border border-admin-neutral-light dark:border-white/5">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-6 flex items-center justify-between">
                                    <span className="flex items-center gap-2">
                                        <span className="material-symbols-outlined text-admin-primary text-[20px]">hive</span>
                                        Model Ensemble Votes
                                    </span>
                                    <span className="text-[10px] text-slate-400 font-normal">N = 4 MODELS</span>
                                </h3>
                                <div className="space-y-6">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-[#ffaf87]"></div>
                                                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">BLIP</span>
                                            </div>
                                            <span className="text-sm font-bold text-slate-900 dark:text-white">88.4%</span>
                                        </div>
                                        <div className="w-full bg-slate-100 dark:bg-white/5 rounded-full h-2">
                                            <div className="bg-[#ffaf87] h-2 rounded-full" style={{ width: "88.4%" }}></div>
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-[#ff8e72]"></div>
                                                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">CLIP</span>
                                            </div>
                                            <span className="text-sm font-bold text-slate-900 dark:text-white">91.2%</span>
                                        </div>
                                        <div className="w-full bg-slate-100 dark:bg-white/5 rounded-full h-2">
                                            <div className="bg-[#ff8e72] h-2 rounded-full" style={{ width: "91.2%" }}></div>
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-[#4ce0b3]"></div>
                                                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">SigLIP2</span>
                                            </div>
                                            <span className="text-sm font-bold text-slate-900 dark:text-white">99.1%</span>
                                        </div>
                                        <div className="w-full bg-slate-100 dark:bg-white/5 rounded-full h-2">
                                            <div className="bg-[#4ce0b3] h-2 rounded-full shadow-[0_0_10px_rgba(76,224,179,0.5)]" style={{ width: "99.1%" }}></div>
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-[#377771]"></div>
                                                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Qwen-VL</span>
                                            </div>
                                            <span className="text-sm font-bold text-slate-900 dark:text-white">97.5%</span>
                                        </div>
                                        <div className="w-full bg-slate-100 dark:bg-white/5 rounded-full h-2">
                                            <div className="bg-[#377771] h-2 rounded-full" style={{ width: "97.5%" }}></div>
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
