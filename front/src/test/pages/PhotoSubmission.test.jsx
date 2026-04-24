import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PhotoSubmission from '../../pages/PhotoSubmission';
import { useMission } from '../../hooks/useMission';
import { useMissionStore } from '../../store/useMissionStore';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../../hooks/useMission');
vi.mock('../../store/useMissionStore');

describe('PhotoSubmission — stale state race condition (BUG 1)', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    useMissionStore.mockReturnValue({
      missionId: 'test-mission-123',
      missionType: 'location',
      hint: 'Test hint',
    });
  });

  it('3번째 실패 후에만 /mission/result로 이동한다', async () => {
    const submitPhoto = vi.fn().mockResolvedValue({ success: false, message: 'Wrong photo' });
    useMission.mockReturnValue({ submitPhoto, isLoading: false });

    render(
      <MemoryRouter>
        <PhotoSubmission />
      </MemoryRouter>
    );

    const fileInput = document.querySelector('input[type="file"]');
    const fakeFile = new File(['img'], 'photo.jpg', { type: 'image/jpeg' });
    fireEvent.change(fileInput, { target: { files: [fakeFile] } });

    const btn = screen.getByText('인증 제출');

    // 1차 실패 — navigate 없어야 함
    fireEvent.click(btn);
    await waitFor(() => expect(submitPhoto).toHaveBeenCalledTimes(1));
    expect(mockNavigate).not.toHaveBeenCalledWith('/mission/result');

    // 2차 실패 — navigate 없어야 함
    fireEvent.click(btn);
    await waitFor(() => expect(submitPhoto).toHaveBeenCalledTimes(2));
    expect(mockNavigate).not.toHaveBeenCalledWith('/mission/result');

    // 3차 실패 — 반드시 navigate 해야 함
    fireEvent.click(btn);
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/mission/result'));
  });
});

describe('PhotoSubmission — route guard (BUG 4)', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
  });

  it('missionId가 null이면 "/"로 redirect한다', async () => {
    useMission.mockReturnValue({ submitPhoto: vi.fn(), isLoading: false });
    useMissionStore.mockReturnValue({
      missionId: null,
      missionType: 'location',
      hint: null,
    });

    render(
      <MemoryRouter>
        <PhotoSubmission />
      </MemoryRouter>
    );

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('missionId가 있으면 redirect하지 않는다', () => {
    useMission.mockReturnValue({ submitPhoto: vi.fn(), isLoading: false });
    useMissionStore.mockReturnValue({
      missionId: 'active-mission-999',
      missionType: 'location',
      hint: 'Some hint',
    });

    render(
      <MemoryRouter>
        <PhotoSubmission />
      </MemoryRouter>
    );

    expect(mockNavigate).not.toHaveBeenCalledWith('/');
  });
});
