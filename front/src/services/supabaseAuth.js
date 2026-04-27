import { createClient } from '@supabase/supabase-js';

const CLIENT_KEY_PATTERN = /^(sb_publishable_|eyJ)/;
const SESSION_STORAGE_KEY = 'pazule.supabase.session';
let supabaseClient = null;

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(
    normalized.length + ((4 - (normalized.length % 4)) % 4),
    '=',
  );
  return atob(padded);
}

export function getSupabaseClientConfig(env = import.meta.env) {
  const supabaseUrl = env.VITE_SUPABASE_URL;
  const publishableKey =
    env.VITE_SUPABASE_PUBLISHABLE_KEY || env.VITE_SUPABASE_ANON_KEY;
  const missing = [];

  if (!supabaseUrl) {
    missing.push('VITE_SUPABASE_URL');
  }
  if (!publishableKey) {
    missing.push('VITE_SUPABASE_PUBLISHABLE_KEY');
  }
  if (missing.length > 0) {
    throw new Error(`Missing ${missing.join(', ')} for Supabase OAuth.`);
  }
  if (!CLIENT_KEY_PATTERN.test(publishableKey)) {
    throw new Error(
      'Supabase OAuth requires a frontend-safe publishable or legacy anon key.',
    );
  }

  return {
    supabaseUrl: supabaseUrl.replace(/\/+$/, ''),
    publishableKey,
  };
}

export function buildGoogleOAuthUrl({
  supabaseUrl,
  redirectTo = `${window.location.origin}/auth/callback`,
}) {
  const url = new URL('/auth/v1/authorize', supabaseUrl);
  url.searchParams.set('provider', 'google');
  url.searchParams.set('redirect_to', redirectTo);
  return url;
}

export function getSupabaseClient(env = import.meta.env) {
  const { supabaseUrl, publishableKey } = getSupabaseClientConfig(env);
  if (!supabaseClient) {
    supabaseClient = createClient(supabaseUrl, publishableKey, {
      auth: {
        flowType: 'pkce',
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }
  return supabaseClient;
}

export async function startGoogleOAuth({
  env = import.meta.env,
  client = getSupabaseClient(env),
  redirectTo = `${window.location.origin}/auth/callback`,
} = {}) {
  const { data, error } = await client.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
    },
  });
  if (error) {
    throw error;
  }
  return data;
}

export function parseOAuthCallback(hash = window.location.hash) {
  const params = new URLSearchParams(hash.replace(/^#/, ''));
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');
  const expiresIn = Number(params.get('expires_in') || 0);
  const tokenType = params.get('token_type') || 'bearer';

  if (!accessToken || !refreshToken) {
    throw new Error('Supabase OAuth callback did not include session tokens.');
  }

  const user = getUserFromAccessToken(accessToken);

  return {
    accessToken,
    refreshToken,
    expiresIn,
    tokenType,
    userId: user.userId,
    email: user.email,
  };
}

export function getUserFromAccessToken(accessToken) {
  const [, payload] = accessToken.split('.');
  if (!payload) {
    throw new Error('Supabase access token is not a JWT.');
  }
  const claims = JSON.parse(decodeBase64Url(payload));
  if (!claims.sub) {
    throw new Error('Supabase access token did not include a user id.');
  }
  return {
    userId: claims.sub,
    email: claims.email ?? null,
  };
}

export function persistSupabaseSession(
  session,
  storage = window.localStorage,
) {
  storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function getStoredSupabaseSession(storage = window.localStorage) {
  const raw = storage.getItem(SESSION_STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function getCurrentSupabaseSession(client = getSupabaseClient()) {
  const { data, error } = await client.auth.getSession();
  if (error) {
    throw error;
  }
  const session = data.session;
  if (!session?.access_token || !session?.refresh_token) {
    return null;
  }
  const user = session.user ?? getUserFromAccessToken(session.access_token);
  return {
    accessToken: session.access_token,
    refreshToken: session.refresh_token,
    expiresIn: session.expires_in ?? 0,
    tokenType: session.token_type ?? 'bearer',
    userId: user.id ?? user.userId,
    email: user.email ?? null,
  };
}
