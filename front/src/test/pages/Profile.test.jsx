import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Profile from '../../pages/Profile';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  resetAll: vi.fn(),
  clearSession: vi.fn(),
  getUserStats: vi.fn(),
  resetUserData: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mocks.navigate };
});

vi.mock('../../services/api', () => ({
  api: {
    getUserStats: mocks.getUserStats,
    resetUserData: mocks.resetUserData,
  },
}));

vi.mock('../../store/useAuthStore', () => ({
  useAuthStore: vi.fn(() => ({
    userId: 'user-1',
    email: 'demo@example.com',
    accessToken: 'demo-token',
    isAuthenticated: true,
    clearSession: mocks.clearSession,
  })),
}));

vi.mock('../../store/useMissionStore', () => ({
  useMissionStore: vi.fn(() => ({
    resetAll: mocks.resetAll,
  })),
}));

function renderProfile() {
  return render(
    <MemoryRouter>
      <Profile />
    </MemoryRouter>,
  );
}

describe('Profile actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getUserStats.mockResolvedValue({
      total_attempts: 3,
      success_location: 2,
      success_atmosphere: 1,
      total_coupons: 2,
      history: [],
    });
    mocks.resetUserData.mockResolvedValue({});
  });

  it('renders wallet and danger actions with the shared card pattern', async () => {
    renderProfile();

    expect(await screen.findByRole('heading', { name: '쿠폰 지갑 보기' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '위험 영역' })).toBeInTheDocument();

    const actionCards = screen.getAllByTestId('profile-action-card');
    expect(actionCards).toHaveLength(2);

    actionCards.forEach((card) => {
      expect(card).toHaveClass('rounded-2xl');
      expect(card).toHaveClass('border');
      expect(card).toHaveClass('shadow-card');

      const button = within(card).getByRole('button');
      expect(button).toHaveClass('h-11');
      expect(button).toHaveClass('w-full');
      expect(button).toHaveClass('rounded-xl');
      expect(button).not.toHaveClass('underline');
    });
  });

  it('navigates to the coupon wallet from the wallet action', async () => {
    renderProfile();

    fireEvent.click(await screen.findByRole('button', { name: /쿠폰 지갑으로 이동/ }));

    expect(mocks.navigate).toHaveBeenCalledWith('/wallet');
  });

  it('confirms and resets all profile data from the danger action', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderProfile();

    fireEvent.click(await screen.findByRole('button', { name: /모든 데이터 초기화/ }));

    await waitFor(() => {
      expect(mocks.resetUserData).toHaveBeenCalledWith('user-1', 'demo-token');
    });
    expect(mocks.resetAll).toHaveBeenCalled();
    expect(mocks.navigate).toHaveBeenCalledWith('/');
    confirmSpy.mockRestore();
  });
});
