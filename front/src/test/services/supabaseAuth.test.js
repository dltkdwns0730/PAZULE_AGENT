import {
  buildGoogleOAuthUrl,
  getSupabaseClientConfig,
  getUserFromAccessToken,
  startGoogleOAuth,
  parseOAuthCallback,
} from '../../services/supabaseAuth';

describe('supabaseAuth', () => {
  it('builds a Gmail OAuth authorize URL with the configured redirect target', () => {
    const url = buildGoogleOAuthUrl({
      supabaseUrl: 'https://project.supabase.co',
      redirectTo: 'http://localhost:5173/auth/callback',
    });

    expect(url.origin).toBe('https://project.supabase.co');
    expect(url.pathname).toBe('/auth/v1/authorize');
    expect(url.searchParams.get('provider')).toBe('google');
    expect(url.searchParams.get('redirect_to')).toBe(
      'http://localhost:5173/auth/callback',
    );
  });

  it('requires frontend-safe Supabase config instead of server secrets', () => {
    expect(() => getSupabaseClientConfig({})).toThrow(
      /VITE_SUPABASE_PUBLISHABLE_KEY/,
    );
    expect(() =>
      getSupabaseClientConfig({
        VITE_SUPABASE_URL: 'https://project.supabase.co',
        VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_secret_bad',
      }),
    ).toThrow(/frontend-safe/);
  });

  it('accepts publishable and legacy anon keys for browser auth', () => {
    expect(
      getSupabaseClientConfig({
        VITE_SUPABASE_URL: 'https://project.supabase.co',
        VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_abc',
      }),
    ).toEqual({
      supabaseUrl: 'https://project.supabase.co',
      publishableKey: 'sb_publishable_abc',
    });

    expect(
      getSupabaseClientConfig({
        VITE_SUPABASE_URL: 'https://project.supabase.co',
        VITE_SUPABASE_PUBLISHABLE_KEY: 'eyJhbGciOiJIUzI1NiJ9.abc.def',
      }).publishableKey,
    ).toMatch(/^eyJ/);
  });

  it('accepts VITE_SUPABASE_ANON_KEY as a frontend-safe fallback', () => {
    expect(
      getSupabaseClientConfig({
        VITE_SUPABASE_URL: 'https://project.supabase.co',
        VITE_SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiJ9.abc.def',
      }).publishableKey,
    ).toMatch(/^eyJ/);
  });

  it('parses Supabase OAuth callback tokens from the URL hash', () => {
    const accessToken = [
      'header',
      btoa(JSON.stringify({ sub: 'user-123', email: 'user@example.com' })),
      'signature',
    ].join('.');

    expect(
      parseOAuthCallback(
        `#access_token=${accessToken}&refresh_token=refresh-123&expires_in=3600&token_type=bearer`,
      ),
    ).toEqual({
      accessToken,
      refreshToken: 'refresh-123',
      expiresIn: 3600,
      tokenType: 'bearer',
      userId: 'user-123',
      email: 'user@example.com',
      isAdmin: false,
    });
  });

  it('extracts user id and email from a JWT access token payload', () => {
    const token = [
      'header',
      btoa(JSON.stringify({ sub: 'supabase-user-id', email: 'a@b.test' })),
      'signature',
    ].join('.');

    expect(getUserFromAccessToken(token)).toEqual({
      userId: 'supabase-user-id',
      email: 'a@b.test',
      isAdmin: false,
    });
  });

  it('starts Google OAuth through Supabase Auth client', async () => {
    const signInWithOAuth = vi.fn().mockResolvedValue({
      data: { provider: 'google' },
      error: null,
    });

    await expect(
      startGoogleOAuth({
        client: { auth: { signInWithOAuth } },
        redirectTo: 'http://localhost:5173/auth/callback',
      }),
    ).resolves.toEqual({ provider: 'google' });

    expect(signInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: {
        redirectTo: 'http://localhost:5173/auth/callback',
      },
    });
  });
});
