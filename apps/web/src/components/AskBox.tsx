import React, { useState } from 'react';

interface AskBoxProps {
  currentTime: number;
  onPause: () => void;
  onSubmit: (query: string, pause_t: number) => void;
  isLoading?: boolean;
}

export function formatSeconds(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

export const AskBox: React.FC<AskBoxProps> = ({
  currentTime,
  onPause,
  onSubmit,
  isLoading = false,
}) => {
  const [query, setQuery] = useState('');
  const [lockedPauseTime, setLockedPauseTime] = useState<number | null>(null);

  const handleFocus = () => {
    onPause();
    if (lockedPauseTime === null) {
      setLockedPauseTime(currentTime);
    }
  };

  const currentDisplayTime = lockedPauseTime !== null ? lockedPauseTime : currentTime;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    const timeToSend = lockedPauseTime !== null ? lockedPauseTime : currentTime;
    onSubmit(query.trim(), timeToSend);
    setQuery('');
    setLockedPauseTime(null);
  };

  return (
    <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-amber)' }}></span>
          <span>Asking at {formatSeconds(currentDisplayTime)}</span>
        </span>
        {lockedPauseTime !== null && (
          <button
            type="button"
            onClick={() => setLockedPauseTime(currentTime)}
            style={{ color: 'var(--accent-primary)', fontSize: '0.75rem' }}
          >
            Update to now ({formatSeconds(currentTime)})
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={handleFocus}
          placeholder="Ask anything up to this moment..."
          disabled={isLoading}
          aria-label="Ask question input"
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-primary)',
            color: '#fff',
            fontWeight: 600,
            opacity: isLoading || !query.trim() ? 0.6 : 1,
          }}
        >
          {isLoading ? '...' : 'Ask'}
        </button>
      </form>
    </div>
  );
};
