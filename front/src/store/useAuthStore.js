import { create } from 'zustand';
import {
  getStoredSupabaseSession,
  persistSupabaseSession,
} from '../services/supabaseAuth';

const storedSession = getStoredSupabaseSession();

export const useAuthStore = create((set) => ({
  userId: storedSession?.userId ?? null,
  email: storedSession?.email ?? null,
  accessToken: storedSession?.accessToken ?? null,
  refreshToken: storedSession?.refreshToken ?? null,
  isAuthenticated: Boolean(storedSession?.userId && storedSession?.accessToken),

  setSession: (session) => {
    persistSupabaseSession(session);
    set({
      userId: session.userId,
      email: session.email ?? null,
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      isAuthenticated: true,
    });
  },

  clearSession: () => {
    window.localStorage.removeItem('pazule.supabase.session');
    set({
      userId: null,
      email: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },
}));
