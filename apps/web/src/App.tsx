import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import { Library } from './pages/Library';
import { Login } from './pages/Login';
import { Upload } from './pages/Upload';
import { Watch } from './pages/Watch';
import { Video } from './api/types';

export const App: React.FC = () => {
  const { user, login, logout, isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<'library' | 'upload' | 'watch'>('library');
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  if (!isAuthenticated) {
    return <Login onLogin={login} />;
  }

  const handleSelectVideo = (v: Video) => {
    setSelectedVideo(v);
    setCurrentView('watch');
  };

  const handleVideoCreated = (v: Video) => {
    setSelectedVideo(v);
    setCurrentView('watch');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Global Navbar */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 24px',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        <div
          onClick={() => setCurrentView('library')}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
        >
          <span style={{ fontSize: '1.4rem' }}>🎓</span>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.5px' }}>
            AskQuiz<span style={{ color: 'var(--accent-primary)' }}>.IQ</span>
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            {user?.email}
          </span>
          <button
            onClick={logout}
            style={{
              padding: '6px 12px',
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>
        {currentView === 'library' && (
          <Library
            onSelectVideo={handleSelectVideo}
            onNewUpload={() => setCurrentView('upload')}
          />
        )}
        {currentView === 'upload' && (
          <Upload
            onVideoCreated={handleVideoCreated}
            onCancel={() => setCurrentView('library')}
          />
        )}
        {currentView === 'watch' && selectedVideo && (
          <Watch
            video={selectedVideo}
            onBack={() => setCurrentView('library')}
          />
        )}
      </main>
    </div>
  );
};

export default App;
