import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { AskBox } from '../components/AskBox';

describe('AskBox Component', () => {
  it('pauses player on input focus and sends exact pause_t on submit', () => {
    const onPause = vi.fn();
    const onSubmit = vi.fn();
    const mockTime = 42.5;

    render(
      <AskBox
        currentTime={mockTime}
        onPause={onPause}
        onSubmit={onSubmit}
      />
    );

    // 1. Verify 'Asking at 00:42' is shown
    expect(screen.getByText(/Asking at 00:42/i)).toBeTruthy();

    const input = screen.getByLabelText(/Ask question input/i);

    // 2. Focus input -> must trigger onPause
    fireEvent.focus(input);
    expect(onPause).toHaveBeenCalledTimes(1);

    // 3. Type question and submit
    fireEvent.change(input, { target: { value: 'What is happening right now?' } });
    fireEvent.submit(input.closest('form')!);

    // 4. Verify request body pause_t equals player time at moment of sending
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith('What is happening right now?', mockTime);
  });
});
