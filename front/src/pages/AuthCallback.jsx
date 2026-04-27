import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getCurrentSupabaseSession,
  parseOAuthCallback,
} from '../services/supabaseAuth';
import { useAuthStore } from '../store/useAuthStore';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const { setSession } = useAuthStore();

  useEffect(() => {
    const completeLogin = async () => {
      try {
        const session = await getCurrentSupabaseSession();
        setSession(session ?? parseOAuthCallback());
        window.history.replaceState(null, '', '/auth/callback');
        navigate('/profile', { replace: true });
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : '로그인 처리에 실패했습니다.');
      }
    };

    completeLogin();
  }, [navigate, setSession]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-6 text-dark-teal">
      {error ? (
        <p className="text-sm font-semibold text-red-500">{error}</p>
      ) : (
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-dark-teal border-t-transparent" />
      )}
    </div>
  );
}
