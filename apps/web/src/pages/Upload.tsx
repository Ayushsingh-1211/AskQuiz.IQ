import React, { useState } from 'react';
import { api } from '../api/client';
import { Video } from '../api/types';

interface UploadProps {
  onVideoCreated: (video: Video) => void;
  onCancel: () => void;
}

export const Upload: React.FC<UploadProps> = ({ onVideoCreated, onCancel }) => {
  const [tab, setTab] = useState<'file' | 'url'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let created: Video;
      if (tab === 'file') {
        if (!file) {
          setError('Please select a video file.');
          setLoading(false);
          return;
        }
        created = await api.uploadVideo(file, title.trim() || undefined);
      } else {
        if (!url.trim()) {
          setError('Please provide a valid video URL.');
          setLoading(false);
          return;
        }
        created = await api.createVideoFromUrl(url.trim(), title.trim() || undefined);
      }
      onVideoCreated(created);
    } catch (err: any) {
      setError(err?.message || 'Failed to ingest video.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '40px auto', padding: '24px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
      <h2 style={{ fontSize: '1.3rem', fontWeight: 600, marginBottom: '16px' }}>Add Video to Learn</h2>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          type="button"
          onClick={() => setTab('file')}
          style={{
            flex: 1,
            padding: '10px',
            background: tab === 'file' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: '#fff',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 500,
          }}
        >
          📁 Upload MP4 File
        </button>
        <button
          type="button"
          onClick={() => setTab('url')}
          style={{
            flex: 1,
            padding: '10px',
            background: tab === 'url' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: '#fff',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 500,
          }}
        >
          🔗 Video / YouTube URL
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px', marginBottom: '16px', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--accent-red)', borderRadius: 'var(--radius-sm)', color: '#fca5a5', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
            Video Title (Optional)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Introduction to Neural Networks"
            style={{ width: '100%', padding: '10px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
          />
        </div>

        {tab === 'file' ? (
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
              Select Video File (MP4, MKV, WebM — Max 2GB)
            </label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              required
              style={{ width: '100%', padding: '10px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
            />
          </div>
        ) : (
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
              Video URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              required
              style={{ width: '100%', padding: '10px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
          <button
            type="button"
            onClick={onCancel}
            style={{ padding: '10px 16px', background: 'var(--bg-tertiary)', color: '#fff', borderRadius: 'var(--radius-sm)' }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            style={{ padding: '10px 20px', background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, borderRadius: 'var(--radius-sm)' }}
          >
            {loading ? 'Processing...' : 'Start Learning'}
          </button>
        </div>
      </form>
    </div>
  );
};
