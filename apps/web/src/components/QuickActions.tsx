import React from 'react';

interface QuickActionsProps {
  onActionClick: (promptText: string) => void;
  disabled?: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onActionClick, disabled = false }) => {
  const actions = [
    { label: '💡 Explain simpler', prompt: 'Can you explain this part in simpler terms?' },
    { label: '📖 Analogy/Example', prompt: 'Give me a real-world analogy or example for what was just explained.' },
    { label: '📝 Summarize so far', prompt: 'Can you summarize what was covered up to this moment?' },
    { label: '📍 Where discussed?', prompt: 'Where in the lecture was this topic first introduced?' },
    { label: '🎯 Quiz me', prompt: 'Ask me a quick check question about the material up to here.' },
  ];

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', margin: '10px 0' }}>
      {actions.map((act, i) => (
        <button
          key={i}
          type="button"
          disabled={disabled}
          onClick={() => onActionClick(act.prompt)}
          style={{
            fontSize: '0.8rem',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            opacity: disabled ? 0.6 : 1,
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          {act.label}
        </button>
      ))}
    </div>
  );
};
