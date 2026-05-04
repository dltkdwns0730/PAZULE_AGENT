import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Login from '../../pages/Login';

const mockNavigate = vi.fn();
const mockSetSession = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../../services/supabaseAuth', () => ({
  createDemoSession: vi.fn((role) => ({
    isAdmin: role === 'admin',
    role,
  })),
  startGoogleOAuth: vi.fn(),
}));

vi.mock('../../store/useAuthStore', () => ({
  useAuthStore: vi.fn((selector) => selector({ setSession: mockSetSession })),
}));

describe('Login viewport layout', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockSetSession.mockReset();
  });

  it('renders the primary login actions', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: 'Google 계정으로 로그인' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /사용자 데모/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /관리자 데모/ })).toBeInTheDocument();
  });

  it('scrolls inside the app frame instead of forcing a viewport-height child', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    const screenRoot = screen.getByTestId('login-screen');

    expect(screenRoot).toHaveClass('h-full');
    expect(screenRoot).toHaveClass('min-h-0');
    expect(screenRoot).toHaveClass('overflow-y-auto');
    expect(screenRoot).not.toHaveClass('min-h-dvh');
  });
});
