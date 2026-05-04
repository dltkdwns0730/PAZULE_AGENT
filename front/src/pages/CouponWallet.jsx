import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { useMissionStore } from '../store/useMissionStore';

export default function CouponWallet() {
    const navigate = useNavigate();
    const { setCoupon } = useMissionStore();
    const { userId, accessToken, isAuthenticated } = useAuthStore();
    const [coupons, setCoupons] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchCoupons = async () => {
        setIsLoading(true);
        if (!isAuthenticated || !userId || !accessToken) {
            navigate('/login', { replace: true });
            return;
        }
        try {
            const data = await api.getCoupons(userId, accessToken);
            const sorted = [...data].sort((a, b) =>
                new Date(b.issued_at) - new Date(a.issued_at)
            );
            setCoupons(sorted);
        } catch {
            // 쿠폰 목록 로드 실패 — 빈 상태 유지
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCoupons();
    }, [accessToken, isAuthenticated, navigate, userId]);

    const handleCouponClick = (coupon) => {
        if (coupon.status === 'redeemed' || coupon.status === 'expired') return;
        setCoupon(coupon);
        navigate('/scan');
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-50">
                <div className="w-8 h-8 rounded-full border-4 border-coral-start border-t-transparent animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="font-display h-full w-full bg-gray-50 flex flex-col relative overflow-hidden antialiased">
            
            {/* Header / Summary Area */}
            <div className="bg-gradient-to-br from-coral-start to-coral-end pt-12 pb-8 px-6 text-white shrink-0 rounded-b-3xl shadow-sm z-10 relative">
                <div className="flex justify-between items-center mb-6">
                    <button onClick={() => navigate('/')} className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center">
                        <span className="material-symbols-outlined text-white">arrow_back</span>
                    </button>
                    <h1 className="text-2xl font-extrabold tracking-tight drop-shadow-sm">쿠폰 지갑</h1>
                    <button onClick={() => navigate('/profile')} className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center hover:bg-white/30 transition-colors">
                        <span className="material-symbols-outlined text-white">person</span>
                    </button>
                </div>

                <div className="flex items-center gap-4 bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 shadow-inner">
                    <div className="w-12 h-12 rounded-full bg-white/30 flex items-center justify-center text-2xl font-bold shadow-sm">
                        {coupons.length}
                    </div>
                    <div>
                        <p className="text-xs text-white/90 font-medium tracking-wide">보유 쿠폰</p>
                        <p className="text-xl font-bold">{coupons.length}개의 쿠폰</p>
                    </div>
                </div>
            </div>

            {/* Coupon List Area */}
            <div className="flex-1 overflow-y-auto no-scrollbar px-6 py-6 space-y-4 bg-gray-50 relative z-0 pb-28">

                <div className="flex justify-between items-center mb-2 px-1">
                    <h2 className="text-sm font-bold text-gray-500 uppercase tracking-widest">사용 가능한 쿠폰</h2>
                    <span className="text-xs font-semibold text-coral-end bg-coral-start/10 px-2 py-1 rounded-md">최신순</span>
                </div>

                {coupons.length > 0 ? (
                    coupons.map((coupon, idx) => (
                        <div 
                            key={idx}
                            onClick={() => handleCouponClick(coupon)}
                            className={`bg-white rounded-2xl p-4 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] flex items-center gap-4 border border-gray-100 transition-transform active:scale-[0.98] cursor-pointer hover:shadow-lg hover:border-coral-start/30 ${coupon.status === 'redeemed' || coupon.status === 'expired' ? 'opacity-60 grayscale-[30%]' : ''}`}
                        >
                            <div className={`w-16 h-16 rounded-xl flex-shrink-0 flex items-center justify-center border overflow-hidden shadow-inner ${coupon.mission_type === 'mission1' ? 'bg-orange-50 border-orange-100 text-coral-end' : 'bg-blue-50 border-blue-100 text-blue-400'}`}>
                                <span className="material-symbols-outlined text-3xl">
                                    {coupon.mission_type === 'mission1' ? 'location_on' : 'filter_vintage'}
                                </span>
                            </div>
                            <div className="flex-1">
                                <h3 className="font-bold text-gray-900 text-[15px] mb-0.5">{coupon.answer} 미션</h3>
                                <p className="text-coral-end font-extrabold text-lg leading-tight">{coupon.discount_rule}</p>
                                <p className="text-[10px] text-gray-400 font-medium mt-1">
                                    {coupon.status === 'redeemed' ? '사용 완료' : coupon.status === 'expired' ? '만료됨' : `만료일 ${new Date(coupon.expires_at).toLocaleDateString()}`}
                                </p>
                            </div>
                            <div className="w-12 h-12 flex-shrink-0 bg-gray-50 rounded-lg p-1 border border-gray-100 shadow-inner flex items-center justify-center">
                                <span className={`material-symbols-outlined text-[28px] ${coupon.status === 'issued' ? 'text-coral-end' : 'text-gray-300'}`}>
                                    {coupon.status === 'redeemed' ? 'check_circle' : 'qr_code_2'}
                                </span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="py-20 text-center flex flex-col items-center justify-center">
                        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-gray-300">
                            <span className="material-symbols-outlined text-4xl">confirmation_number</span>
                        </div>
                        <p className="text-gray-400 font-medium">아직 발급된 쿠폰이 없습니다.</p>
                        <p className="text-gray-300 text-xs mt-1">미션을 완료하고 첫 쿠폰을 받아보세요.</p>
                        <button 
                            onClick={() => navigate('/')}
                            className="mt-6 px-6 py-2.5 bg-coral-start text-white rounded-full font-bold text-sm shadow-lg shadow-coral-start/20 active:scale-95 transition-transform"
                        >
                            미션 보러 가기
                        </button>
                    </div>
                )}
            </div>

        </div>
    );
}

