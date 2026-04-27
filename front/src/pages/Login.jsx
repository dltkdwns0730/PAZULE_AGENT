import { useState } from 'react';
import { LogIn, MapPin, Ticket } from 'lucide-react';
import { startGoogleOAuth } from '../services/supabaseAuth';

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
      <main className="mx-auto flex min-h-screen w-full max-w-md flex-col px-6 pb-8 pt-10">
        <header className="mb-10 flex items-center justify-between">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-coral-end">
              PAZULE
            </p>
            <p className="mt-1 text-sm font-bold text-gray-400">파주 미션 리워드</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-warm-cream">
            <MapPin size={23} className="text-coral-end" aria-hidden="true" />
          </div>
        </header>

        <section className="mb-8">
          <h1 className="text-4xl font-black leading-tight">
            파주를 걷고,
            <br />
            미션을 완료하고,
            <br />
            쿠폰을 받으세요.
          </h1>
          <p className="mt-5 text-base font-medium leading-relaxed text-gray-500">
            로그인하면 미션 기록과 쿠폰 지갑이 내 계정에 저장됩니다.
          </p>
        </section>

        <button
          type="button"
          onClick={handleLogin}
          disabled={isStarting}
          className="mb-4 flex h-14 w-full items-center justify-center gap-2 rounded-lg bg-dark-teal px-4 text-base font-black text-white shadow-lg shadow-dark-teal/20 transition-transform active:scale-[0.98] disabled:opacity-70"
        >
          <LogIn size={20} aria-hidden="true" />
          {isStarting ? 'Google로 이동 중' : 'Google로 로그인'}
        </button>

        {error ? (
          <p className="mb-6 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold leading-relaxed text-red-600">
            {error}
          </p>
        ) : null}

        <section className="grid grid-cols-2 gap-3">
          <InfoBox icon={MapPin} title="오늘의 장소" text="힌트를 보고 미션 장소를 찾습니다." />
          <InfoBox icon={Ticket} title="내 쿠폰" text="성공한 미션은 쿠폰으로 저장됩니다." />
        </section>

        <p className="mt-auto pt-8 text-center text-xs font-medium text-gray-400">
          기업 계정은 로그인 후 권한으로 구분됩니다.
        </p>
      </main>
    </div>
  );
}

function InfoBox({ icon: Icon, title, text }) {
  return (
    <div className="rounded-lg border border-gray-100 bg-warm-cream p-4">
      <Icon size={20} className="text-coral-end" aria-hidden="true" />
      <p className="mt-3 text-sm font-black">{title}</p>
      <p className="mt-1 text-xs leading-relaxed text-gray-500">{text}</p>
    </div>
  );
}
