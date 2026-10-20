import React from 'react';
import { formatSeconds } from './AskBox';

interface UnlockBarProps {
  currentTime: number;
  duration: number;
}

export const UnlockBar: React.FC<UnlockBarProps> = ({ currentTime, duration }) => {
  const percent = duration > 0 ? Math.min(100, Math.max(0, (currentTime / duration) * 100)) : 0;

  return (
    <div style={{ margin: '12px 0', padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
        <span>Material Unlocked: {formatSeconds(currentTime)} / {formatSeconds(duration)}</span>
        <span>{Math.round(percent)}% watched</span>
      </div>
      <div style={{ width: '100%', height: '6px', background: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${percent}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #6366f1, #10b981)',
            transition: 'width 0.2s ease',
          }}
        />
      </div>
      <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
        🔒 Material beyond {formatSeconds(currentTime)} remains locked to prevent spoilers.
      </div>
    </div>
  );
};
