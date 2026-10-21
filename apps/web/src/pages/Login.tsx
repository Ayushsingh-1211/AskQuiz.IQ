import React, { useState } from 'react';

interface LoginProps {
  onLogin: (email: string, pass: string) => Promise<any>;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('demo@askquiz.iq');
  const [password, setPassword] = useState('demo12345');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onLogin(email, password);
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '80px auto', padding: '32px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-lg)' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '8px', textAlign: 'center' }}>
        AskQuiz.IQ
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', textAlign: 'center' }}>
        Sign in to your learning workspace
      </p>

      {error && (
        <div style={{ padding: '10px', marginBottom: '16px', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--accent-red)', borderRadius: 'var(--radius-sm)', color: '#fca5a5', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '12px', background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, borderRadius: 'var(--radius-sm)', marginTop: '8px' }}
        >
          {loading ? 'Signing in (waking server)...' : 'Sign In'}
        </button>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '12px' }}>
          Default Demo: demo@askquiz.iq / demo12345
        </p>
      </form>
    </div>
  );
};
