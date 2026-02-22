import { useNavigate } from "react-router-dom";
import { useState } from "react";

export default function Permissions() {
    const navigate = useNavigate();
    const [permissions, setPermissions] = useState({
        camera: false,
        location: false,
        notifications: false
    });

    const togglePermission = (key) => {
        setPermissions(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const handleContinue = () => {
        // Here we would actually request permissions via browser API
        // For now, just navigate
        navigate('/');
    };

    return (
        <div className="flex flex-col h-full bg-surface-light dark:bg-surface-dark font-display relative overflow-hidden">
            <header className="px-6 py-6">
                <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500 dark:text-gray-400">
                    <span className="material-symbols-outlined">arrow_back</span>
                </button>
            </header>

            <main className="flex-1 px-8 pb-8">
                <div className="mb-10 animate-fade-in-up">
                    <h1 className="text-3xl font-black text-gray-900 dark:text-white mb-3">Enable Access</h1>
                    <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                        To provide the best experience, PAZULE needs access to a few things on your device.
                    </p>
                </div>

                <div className="space-y-6">
                    {/* Camera */}
                    <div className="flex items-center justify-between p-4 bg-white dark:bg-[#1e2827] rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 animate-slide-up" style={{ animationDelay: '100ms' }}>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                                <span className="material-symbols-outlined">photo_camera</span>
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-900 dark:text-white">Camera</h3>
                                <p className="text-xs text-gray-500">For mission verification</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={permissions.camera} onChange={() => togglePermission('camera')} />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    {/* Location */}
                    <div className="flex items-center justify-between p-4 bg-white dark:bg-[#1e2827] rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 animate-slide-up" style={{ animationDelay: '200ms' }}>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400">
                                <span className="material-symbols-outlined">location_on</span>
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-900 dark:text-white">Location</h3>
                                <p className="text-xs text-gray-500">To find nearby missions</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={permissions.location} onChange={() => togglePermission('location')} />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    {/* Notifications */}
                    <div className="flex items-center justify-between p-4 bg-white dark:bg-[#1e2827] rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 animate-slide-up" style={{ animationDelay: '300ms' }}>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                                <span className="material-symbols-outlined">notifications</span>
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-900 dark:text-white">Notifications</h3>
                                <p className="text-xs text-gray-500">Updates on new missions</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={permissions.notifications} onChange={() => togglePermission('notifications')} />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                        </label>
                    </div>
                </div>
            </main>

            <div className="p-8 pb-12">
                <button
                    onClick={handleContinue}
                    className="w-full h-14 bg-primary text-white rounded-xl shadow-lg shadow-primary/30 flex items-center justify-center gap-2 font-bold text-lg hover:bg-[#2a5b56] active:scale-[0.98] transition-all"
                >
                    Continue
                </button>
            </div>
        </div>
    );
}
