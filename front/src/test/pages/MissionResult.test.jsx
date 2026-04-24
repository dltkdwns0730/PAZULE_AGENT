import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MissionResult from '../../pages/MissionResult';
import { useMission } from '../../hooks/useMission';
import { useMissionStore } from '../../store/useMissionStore';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../../hooks/useMission');
vi.mock('../../store/useMissionStore');

describe('MissionResult automatic coupon issuance', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
  });

  it('issues a coupon automatically when mission succeeds', async () => {
    const issueCoupon = vi.fn().mockResolvedValue({ code: 'AUTO1234' });
    useMission.mockReturnValue({ issueCoupon, isLoading: false });
    useMissionStore.mockReturnValue({
      submissionResult: { success: true, score: 0.91, message: 'success' },
      coupon: null,
    });

    render(
      <MemoryRouter>
        <MissionResult />
      </MemoryRouter>
    );

    await waitFor(() => expect(issueCoupon).toHaveBeenCalledTimes(1));
  });

  it('uses the success action only to open the QR confirmation screen', async () => {
    const issueCoupon = vi.fn().mockResolvedValue({ code: 'AUTO1234' });
    useMission.mockReturnValue({ issueCoupon, isLoading: false });
    useMissionStore.mockReturnValue({
      submissionResult: { success: true, score: 0.91, message: 'success' },
      coupon: null,
    });

    render(
      <MemoryRouter>
        <MissionResult />
      </MemoryRouter>
    );

    await waitFor(() => expect(issueCoupon).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole('button', { name: /QR|확인|쿠폰/i }));

    expect(issueCoupon).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/coupon/success');
  });
});
