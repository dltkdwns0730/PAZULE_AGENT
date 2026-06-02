import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../../App';

const mockAuthState = vi.hoisted(() => ({
  isAuthenticated: false,
  setSession: vi.fn(),
}));

vi.mock('../../services/supabaseAuth', () => ({
  createDemoSession: vi.fn(),
  startGoogleOAuth: vi.fn(),
}));

vi.mock('../../store/useAuthStore', () => ({
  useAuthStore: vi.fn((selector) => {
    if (typeof selector === 'function') {
      return selector(mockAuthState);
    }
    return mockAuthState;
  }),
}));

describe('App routes', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('loads the login screen for unauthenticated local root entry', async () => {
    render(<App />);

    expect(await screen.findByTestId('login-screen')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '실제 유저 로그인' })).toBeInTheDocument();
  });
});
