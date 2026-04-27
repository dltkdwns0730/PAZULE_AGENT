import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { useMissionStore } from '../store/useMissionStore';

export default function Profile() {
    const navigate = useNavigate();
    const { resetAll } = useMissionStore();
    const { userId, email, accessToken, isAuthenticated, clearSession } = useAuthStore();
    const [stats, setStats] = useState({
        total_attempts: 0,
        success_location: 0,
        success_atmosphere: 0,
        total_coupons: 0,
        history: [],
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            if (!isAuthenticated || !userId || !accessToken) {
                navigate('/login', { replace: true });
                return;
            }
            try {
                setStats(await api.getUserStats(userId, accessToken));
            } catch (error) {
                console.error('Failed to load profile stats:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchStats();
    }, [accessToken, isAuthenticated, navigate, userId]);

    const handleReset = async () => {
        if (!window.confirm('미션 기록과 쿠폰 데이터를 초기화할까요?')) return;
        try {
            await api.resetUserData(userId, accessToken);
            resetAll();
            navigate('/');
        } catch (error) {
            console.error('Failed to reset user data:', error);
            alert('초기화 중 오류가 발생했습니다.');
        }
    };

    const handleLogout = () => {
        clearSession();
        resetAll();
        navigate('/login', { replace: true });
    };

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-white">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-dark-teal border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="font-display flex h-full w-full flex-col bg-white text-dark-teal">
            <header className="flex items-center justify-between bg-white px-6 pt-10">
                <button
                    onClick={() => navigate(-1)}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey"
                >
                    <span className="material-symbols-outlined">arrow_back_ios_new</span>
                </button>
                <h1 className="text-xl font-bold">프로필</h1>
                <button
                    onClick={handleLogout}
                    className="text-sm font-bold text-gray-400"
                >
                    로그아웃
                </button>
            </header>

            <main className="flex-1 overflow-y-auto px-6 py-8">
                <section className="mb-8 flex flex-col items-center text-center">
                    <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full border-4 border-warm-cream bg-pale-coral shadow-sm">
                        <span className="material-symbols-outlined text-5xl text-coral-end">person</span>
                    </div>
                    <h2 className="text-2xl font-extrabold">미션 참가자</h2>
                    <p className="mt-1 max-w-full truncate text-sm text-gray-400">
                        {email || userId}
                    </p>
                </section>

                <section className="mb-8 grid grid-cols-2 gap-4">
                    <StatCard label="총 미션" value={stats.total_attempts} tone="coral" />
                    <StatCard label="쿠폰" value={stats.total_coupons} />
                    <StatCard label="랜드마크" value={stats.success_location} />
                    <StatCard label="분위기" value={stats.success_atmosphere} />
                </section>

                <section className="mb-8">
                    <div className="mb-4 flex items-center justify-between">
                        <h3 className="text-lg font-bold">최근 미션 기록</h3>
                        <span className="text-xs font-medium text-gray-400">최근 5건</span>
                    </div>

                    {stats.history.length > 0 ? (
                        <div className="space-y-3">
                            {stats.history.map((item) => (
                                <div
                                    key={item.mission_id}
                                    className="flex items-center gap-4 rounded-2xl border border-gray-100 bg-light-grey/30 p-4"
                                >
                                    <span className="material-symbols-outlined text-coral-end">
                                        {item.mission_type === 'location' ? 'location_on' : 'filter_vintage'}
                                    </span>
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-sm font-bold">{item.answer}</p>
                                        <p className="text-xs text-gray-400">
                                            {new Date(item.completed_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <span className="material-symbols-outlined text-sm text-gray-300">verified</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="rounded-2xl border-2 border-dashed border-gray-100 bg-light-grey/20 py-10 text-center">
                            <p className="text-sm text-gray-400">아직 완료한 미션이 없습니다.</p>
                        </div>
                    )}
                </section>

                <section className="space-y-3 pb-10">
                    <button
                        onClick={() => navigate('/wallet')}
                        className="flex w-full items-center justify-between rounded-2xl bg-dark-teal p-5 font-bold text-white shadow-lg shadow-dark-teal/20"
                    >
                        <span className="flex items-center gap-3">
                            <span className="material-symbols-outlined">account_balance_wallet</span>
                            쿠폰 지갑 보기
                        </span>
                        <span className="material-symbols-outlined">arrow_forward_ios</span>
                    </button>

                    <button
                        onClick={handleReset}
                        className="w-full rounded-2xl border-2 border-red-50 p-5 font-bold text-red-500 transition-colors hover:bg-red-50"
                    >
                        데이터 초기화
                    </button>
                </section>
            </main>
        </div>
    );
}

function StatCard({ label, value, tone = 'teal' }) {
    const valueClass = tone === 'coral' ? 'text-coral-end' : 'text-dark-teal';
    return (
        <div className="rounded-2xl border border-dark-teal/5 bg-warm-cream p-5">
            <span className={`${valueClass} text-2xl font-black leading-none`}>{value}</span>
            <p className="mt-1 text-xs font-bold uppercase tracking-wider text-gray-500">{label}</p>
        </div>
    );
}
