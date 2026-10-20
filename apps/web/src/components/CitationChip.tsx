import React from 'react';
import { Citation } from '../api/types';

interface CitationChipProps {
  citation: Citation;
  onSeek?: (seconds: number) => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, onSeek }) => {
  const ref = citation.source_ref;
  const label = ref?.label || `Source ${citation.chunk_id}`;
  const timestamp = ref?.timestamp_s;

  const handleClick = () => {
    if (timestamp !== undefined && timestamp !== null && onSeek) {
      onSeek(timestamp);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      title={citation.text || label}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        background: 'rgba(99, 102, 241, 0.15)',
        border: '1px solid rgba(99, 102, 241, 0.4)',
        borderRadius: '6px',
        padding: '2px 8px',
        fontSize: '0.8rem',
        color: '#a5b4fc',
        cursor: timestamp !== undefined ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
      }}
    >
      <span>📌</span>
      <span>{label}</span>
    </button>
  );
};
