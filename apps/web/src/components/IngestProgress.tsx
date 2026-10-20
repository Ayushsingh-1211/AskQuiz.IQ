import React from 'react';

interface IngestProgressProps {
  status: string;
  metadata?: Record<string, any>;
}

export const IngestProgress: React.FC<IngestProgressProps> = ({ status, metadata = {} }) => {
  const isReady = status === 'ready_text' || status === 'ready_full' || status === 'completed';
  const isFailed = status === 'failed';

  if (isReady) return null;

  return (
    <div
      style={{
        padding: '12px 16px',
        margin: '12px 0',
        borderRadius: 'var(--radius-sm)',
        background: isFailed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)',
        border: `1px solid ${isFailed ? 'var(--accent-red)' : 'var(--accent-primary)'}`,
        color: 'var(--text-primary)',
        fontSize: '0.85rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>{isFailed ? '⚠️' : '⚙️'}</span>
        <strong>Processing Video: Stage [{status}]</strong>
      </div>
      {metadata.visual_unavailable && (
        <div style={{ marginTop: '6px', color: 'var(--accent-amber)', fontSize: '0.8rem' }}>
          Notice: {metadata.fallback_notice || 'Visual understanding unavailable; operating in captions-only mode.'}
        </div>
      )}
    </div>
  );
};
