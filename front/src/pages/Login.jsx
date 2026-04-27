import { useState } from 'react';
import { MapPin, Navigation, Ticket } from 'lucide-react';
import { startGoogleOAuth } from '../services/supabaseAuth';

const FLOW_STEPS = [
  {
    step: '01',
    icon: Navigation,
    title: '힌트 확인',
    desc: '오늘의 장소 힌트를 보고 파주 곳곳을 탐험합니다.',
  },
  {
    step: '02',
    icon: MapPin,
    title: '장소 방문',
    desc: '장소를 찾아 사진으로 미션을 인증합니다.',
  },
  {
    step: '03',
    icon: Ticket,
    title: '쿠폰 획득',
    desc: '성공한 미션마다 파주 로컬 쿠폰이 지갑에 적립됩니다.',
  },
];

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

function FlowStep({ step, icon: Icon, title, desc }) {
  return (
    <div className="flex items-start gap-4 rounded-2xl border border-gray-100 bg-warm-cream p-4">
      <div className="flex flex-col items-center gap-1.5">
        <span className="text-[10px] font-black tracking-widest text-coral-end">{step}</span>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-soft">
          <Icon size={18} className="text-dark-teal" aria-hidden="true" />
        </div>
      </div>
      <div className="flex-1 pt-1">
        <p className="text-sm font-black text-dark-teal">{title}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-gray-500">{desc}</p>
      </div>
    </div>
  );
}

export default function Login() {
  const [error, setError] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const handleLogin = async () => {
    setError('');
    setIsStarting(true);
    try {
      await startGoogleOAuth();
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Google 로그인으로 이동하지 못했습니다.',
      );
      setIsStarting(false);
    }
  };

  return (
    <div className="font-display flex min-h-screen bg-white text-dark-teal">
      <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-10 pt-12">

        {/* Brand header */}
        <header className="mb-10">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-dark-teal shadow-btn-strong">
            <MapPin size={24} className="text-white" aria-hidden="true" />
          </div>
          <p className="text-[11px] font-black uppercase tracking-[0.2em] text-coral-end">
            PAZULE
          </p>
          <h1 className="mt-2 text-3xl font-black leading-snug text-dark-teal">
            파주를 걷고,
            <br />
            <span className="text-coral-end">미션</span>을 완료하고,
            <br />
            쿠폰을 받으세요.
          </h1>
          <p className="mt-3 text-sm font-medium leading-relaxed text-gray-500">
            로그인하면 미션 기록과 쿠폰 지갑이 내 계정에 저장됩니다.
          </p>
        </header>

        {/* 3-step mission flow */}
        <section aria-label="미션 플로우" className="mb-8 space-y-3">
          {FLOW_STEPS.map((s) => (
            <FlowStep key={s.step} {...s} />
          ))}
        </section>

        {/* Google login button */}
        <div className="mb-3">
          <button
            type="button"
            onClick={handleLogin}
            disabled={isStarting}
            aria-label="Google 계정으로 로그인"
            className="flex h-14 w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 shadow-card transition-shadow hover:shadow-hover active:scale-[0.98] disabled:opacity-60"
          >
            {isStarting ? (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-dark-teal" />
            ) : (
              <GoogleIcon />
            )}
            {isStarting ? 'Google로 이동 중…' : 'Google 계정으로 시작하기'}
          </button>
        </div>

        {error ? (
          <p
            role="alert"
            className="mb-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold leading-relaxed text-red-600"
          >
            {error}
          </p>
        ) : null}

        <p className="mt-auto pt-6 text-center text-xs font-medium text-gray-400">
          기업 계정은 로그인 후 권한으로 구분됩니다.
        </p>
      </main>
    </div>
  );
}
