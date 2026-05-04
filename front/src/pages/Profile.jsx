import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin,
  Navigation,
  Ticket,
  Sparkles,
  Wallet,
  ChevronRight,
  LogOut,
  ArrowLeft,
} from 'lucide-react';
import { api } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { useMissionStore } from '../store/useMissionStore';

function relativeDate(iso) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (diff === 0) return '오늘';
  if (diff === 1) return '어제';
  if (diff < 7) return `${diff}일 전`;
  return new Date(iso).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function parseNickname(email) {
  if (!email) return '미션 참가자';
  const local = email.split('@')[0];
  return local.length > 12 ? local.slice(0, 12) + '…' : local;
}

const STAT_CONFIG = [
  { key: 'total_attempts', label: '총 미션', icon: Navigation, tone: 'coral' },
  { key: 'total_coupons', label: '쿠폰', icon: Ticket, tone: 'teal' },
  { key: 'success_location', label: '랜드마크', icon: MapPin, tone: 'teal' },
  { key: 'success_atmosphere', label: '분위기', icon: Sparkles, tone: 'teal' },
];

function StatCard({ label, value, icon: Icon, tone }) {
  const isCoral = tone === 'coral';
  return (
    <div className="rounded-2xl border border-dark-teal/5 bg-warm-cream p-4">
      <div className="mb-2 flex items-center justify-between">
        <Icon
          size={16}
          className={isCoral ? 'text-coral-end' : 'text-dark-teal/50'}
          aria-hidden="true"
        />
      </div>
      <span
        className={`text-2xl font-black leading-none ${isCoral ? 'text-coral-end' : 'text-dark-teal'}`}
      >
        {value}
      </span>
      <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">{label}</p>
    </div>
  );
}

function MissionHistoryItem({ item }) {
  const isLocation = item.mission_type === 'location';
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-100 bg-light-grey/30 p-4">
      <div
        className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl ${
          isLocation ? 'bg-pale-coral' : 'bg-warm-cream'
        }`}
      >
        {isLocation ? (
          <MapPin size={16} className="text-coral-end" aria-hidden="true" />
        ) : (
          <Sparkles size={16} className="text-dark-teal" aria-hidden="true" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-bold text-dark-teal">{item.answer}</p>
        <div className="mt-0.5 flex items-center gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
              isLocation
                ? 'bg-pale-coral text-coral-end'
                : 'bg-warm-cream text-dark-teal'
            }`}
          >
            {isLocation ? '랜드마크' : '분위기'}
          </span>
          <span className="text-xs text-gray-400">{relativeDate(item.completed_at)}</span>
        </div>
      </div>
      <Navigation size={14} className="flex-shrink-0 text-gray-300" aria-hidden="true" />
    </div>
  );
}

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
      } catch {
        // 프로필 통계 로드 실패 — 빈 상태 유지
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, [accessToken, isAuthenticated, navigate, userId]);

  const handleReset = async () => {
    if (!window.confirm('미션 기록과 쿠폰 데이터를 초기화할까요?\n이 작업은 되돌릴 수 없습니다.')) return;
    try {
      await api.resetUserData(userId, accessToken);
      resetAll();
      navigate('/');
    } catch {
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

  const nickname = parseNickname(email);

  return (
    <div className="font-display flex h-full w-full flex-col bg-white text-dark-teal">

      {/* Header */}
      <header className="flex items-center justify-between px-6 pt-10 pb-4 bg-white">
        <button
          onClick={() => navigate(-1)}
          aria-label="뒤로 가기"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey transition-colors hover:bg-gray-200"
        >
          <ArrowLeft size={18} className="text-dark-teal" aria-hidden="true" />
        </button>
        <h1 className="text-base font-bold text-dark-teal">프로필</h1>
        <button
          onClick={handleLogout}
          aria-label="로그아웃"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-light-grey transition-colors hover:bg-gray-200"
        >
          <LogOut size={16} className="text-gray-500" aria-hidden="true" />
        </button>
      </header>

      <main className="flex-1 overflow-y-auto">

        {/* User hero */}
        <section className="px-6 pb-6 pt-2 text-center" aria-label="사용자 정보">
          <div className="relative mx-auto mb-4 h-20 w-20">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-coral-start to-coral-end shadow-card">
              <span className="text-3xl font-black text-white">
                {nickname.charAt(0).toUpperCase()}
              </span>
            </div>
            {stats.total_attempts > 0 && (
              <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-dark-teal text-[10px] font-black text-white shadow-sm">
                ✓
              </span>
            )}
          </div>
          <h2 className="text-xl font-extrabold text-dark-teal">{nickname}</h2>
          <p className="mt-0.5 text-xs text-gray-400 max-w-[200px] mx-auto truncate">{email}</p>
        </section>

        {/* Stats grid */}
        <section className="px-6 mb-6" aria-label="미션 통계">
          <div className="grid grid-cols-2 gap-3">
            {STAT_CONFIG.map(({ key, label, icon, tone }) => (
              <StatCard
                key={key}
                label={label}
                value={stats[key]}
                icon={icon}
                tone={tone}
              />
            ))}
          </div>
        </section>

        {/* Mission history */}
        <section className="px-6 mb-6" aria-label="최근 미션 기록">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold text-dark-teal">최근 미션 기록</h3>
            <span className="rounded-full bg-light-grey px-2.5 py-0.5 text-[10px] font-bold text-gray-500">
              최근 5건
            </span>
          </div>

          {stats.history.length > 0 ? (
            <div className="space-y-2">
              {stats.history.map((item) => (
                <MissionHistoryItem key={item.mission_id} item={item} />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border-2 border-dashed border-gray-100 bg-light-grey/20 py-10 text-center">
              <Navigation size={28} className="mx-auto mb-2 text-gray-200" aria-hidden="true" />
              <p className="text-sm font-bold text-gray-400">아직 완료한 미션이 없습니다</p>
              <p className="mt-1 text-xs text-gray-300">첫 미션을 시작해보세요!</p>
            </div>
          )}
        </section>

        {/* Primary CTA */}
        <section className="px-6 mb-4" aria-label="쿠폰 지갑">
          <button
            onClick={() => navigate('/wallet')}
            className="flex w-full items-center justify-between rounded-2xl bg-dark-teal px-5 py-4 font-bold text-white shadow-btn-strong transition-transform active:scale-[0.98]"
          >
            <span className="flex items-center gap-3">
              <Wallet size={20} aria-hidden="true" />
              <span>
                <span className="block text-sm font-black">쿠폰 지갑 보기</span>
                {stats.total_coupons > 0 && (
                  <span className="block text-xs font-medium text-white/70">
                    쿠폰 {stats.total_coupons}장 보유 중
                  </span>
                )}
              </span>
            </span>
            <ChevronRight size={18} className="text-white/70" aria-hidden="true" />
          </button>
        </section>

        {/* Danger zone */}
        <section className="px-6 pb-10" aria-label="위험 영역">
          <div className="rounded-2xl border border-red-50 bg-red-50/40 p-4">
            <p className="mb-2 text-xs font-bold uppercase tracking-wider text-red-400">
              위험 영역
            </p>
            <p className="mb-3 text-xs leading-relaxed text-gray-500">
              미션 기록과 쿠폰 데이터가 영구 삭제됩니다.
            </p>
            <button
              onClick={handleReset}
              className="text-xs font-bold text-red-500 underline underline-offset-2 transition-opacity hover:opacity-70"
            >
              모든 데이터 초기화
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
