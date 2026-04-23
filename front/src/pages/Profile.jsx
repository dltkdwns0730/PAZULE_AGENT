import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMissionStore } from '../store/useMissionStore';

export default function Profile() {
    const navigate = useNavigate();
    const { resetAll } = useMissionStore();
    const [stats, setStats] = useState({
        total_attempts: 0,
        success_location: 0,
        success_atmosphere: 0,
        total_coupons: 0,
        history: []
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('/api/user/stats?user_id=guest');
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (error) {
                console.error('통계 데이터 로드 실패:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchStats();
    }, []);

    const handleReset = async () => {
        if (window.confirm('모든 탐험 기록과 설정을 초기화할까요?')) {
            try {
                // 백엔드 데이터 초기화 호출
                const response = await fetch('/api/user/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'guest' })
                });

                if (response.ok) {
                    resetAll();
                    navigate('/');
                } else {
                    alert('초기화 중 오류가 발생했습니다.');
                }
            } catch (error) {
                console.error('초기화 실패:', error);
                alert('서버와 통신할 수 없습니다.');
            }
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-white">
                <div className="w-8 h-8 rounded-full border-4 border-dark-teal border-t-transparent animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="font-display h-full w-full bg-white flex flex-col relative overflow-hidden">
            
            {/* Header */}
            <header className="pt-10 px-6 flex items-center justify-between flex-shrink-0 bg-white z-20">
                <button onClick={() => navigate(-1)} className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey text-dark-teal">
                    <span className="material-symbols-outlined">arrow_back_ios_new</span>
                </button>
                <h1 className="text-dark-teal text-xl font-bold">내 프로필</h1>
                <div className="w-10 h-10"></div> {/* Spacer */}
            </header>

            <main className="flex-1 overflow-y-auto px-6 py-8 no-scrollbar z-10">
                
                {/* User Info Section */}
                <div className="flex flex-col items-center mb-10">
                    <div className="w-24 h-24 rounded-full bg-pale-coral flex items-center justify-center mb-4 shadow-sm border-4 border-warm-cream">
                        <span className="material-symbols-outlined text-5xl text-coral-end">person</span>
                    </div>
                    <h2 className="text-dark-teal text-2xl font-extrabold mb-1">탐험가님</h2>
                    <p className="text-gray-400 text-sm">파주 출판단지를 여행 중입니다</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4 mb-10">
                    <div className="bg-warm-cream p-5 rounded-[1.5rem] border border-dark-teal/5">
                        <span className="text-coral-end font-black text-2xl leading-none">{stats.total_attempts}</span>
                        <p className="text-gray-500 text-xs font-bold mt-1 uppercase tracking-wider">총 탐험 횟수</p>
                    </div>
                    <div className="bg-warm-cream p-5 rounded-[1.5rem] border border-dark-teal/5">
                        <span className="text-dark-teal font-black text-2xl leading-none">{stats.total_coupons}</span>
                        <p className="text-gray-500 text-xs font-bold mt-1 uppercase tracking-wider">획득한 혜택</p>
                    </div>
                    <div className="bg-white p-5 rounded-[1.5rem] border-2 border-warm-cream">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="material-symbols-outlined text-coral-end text-sm">location_on</span>
                            <span className="text-dark-teal font-black text-lg">{stats.success_location}</span>
                        </div>
                        <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest">랜드마크 마스터</p>
                    </div>
                    <div className="bg-white p-5 rounded-[1.5rem] border-2 border-warm-cream">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="material-symbols-outlined text-dark-teal text-sm">filter_vintage</span>
                            <span className="text-dark-teal font-black text-lg">{stats.success_atmosphere}</span>
                        </div>
                        <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest">분위기 수집가</p>
                    </div>
                </div>

                {/* Recent History */}
                <div className="mb-10">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-dark-teal font-bold text-lg">최근 탐험 기록</h3>
                        <span className="text-gray-400 text-xs font-medium">최근 5건</span>
                    </div>
                    
                    {stats.history.length > 0 ? (
                        <div className="space-y-3">
                            {stats.history.map((item, idx) => (
                                <div key={idx} className="flex items-center gap-4 p-4 bg-light-grey/30 rounded-2xl border border-gray-100">
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${item.mission_type === 'location' ? 'bg-pale-coral text-coral-end' : 'bg-dark-teal/10 text-dark-teal'}`}>
                                        <span className="material-symbols-outlined text-xl">
                                            {item.mission_type === 'location' ? 'location_on' : 'filter_vintage'}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-dark-teal font-bold text-sm">{item.answer}</p>
                                        <p className="text-gray-400 text-xs">{new Date(item.completed_at).toLocaleDateString()}</p>
                                    </div>
                                    <span className="material-symbols-outlined text-gray-300 text-sm font-bold">verified</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="py-10 text-center bg-light-grey/20 rounded-[2rem] border-2 border-dashed border-gray-100">
                            <p className="text-gray-400 text-sm">아직 성공한 탐험 기록이 없습니다.</p>
                        </div>
                    )}
                </div>

                {/* Settings & Danger Zone */}
                <div className="space-y-3 mb-10">
                    <button 
                        onClick={() => navigate('/wallet')}
                        className="w-full flex items-center justify-between p-5 bg-dark-teal text-white rounded-2xl shadow-lg shadow-dark-teal/20"
                    >
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined">account_balance_wallet</span>
                            <span className="font-bold">내 지갑 확인하기</span>
                        </div>
                        <span className="material-symbols-outlined">arrow_forward_ios</span>
                    </button>
                    
                    <button 
                        onClick={handleReset}
                        className="w-full flex items-center justify-center p-5 text-red-500 font-bold border-2 border-red-50 rounded-2xl hover:bg-red-50 transition-colors"
                    >
                        데이터 초기화
                    </button>
                </div>

            </main>
        </div>
    );
}
