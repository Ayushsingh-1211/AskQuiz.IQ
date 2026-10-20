import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Video } from '../api/types';
import { ChatMessage, ChatPanel } from '../components/ChatPanel';
import { IngestProgress } from '../components/IngestProgress';
import { Player } from '../components/Player';
import { QuickActions } from '../components/QuickActions';
import { UnlockBar } from '../components/UnlockBar';
import { usePlayerTime } from '../hooks/usePlayerTime';

interface WatchProps {
  video: Video;
  onBack: () => void;
}

export const Watch: React.FC<WatchProps> = ({ video, onBack }) => {
  const [currentVideo, setCurrentVideo] = useState<Video>(video);
  const {
    currentTime,
    setCurrentTime,
    duration,
    setDuration,
    pause,
    seekTo,
    registerPlayer,
  } = usePlayerTime();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    setCurrentVideo(video);
    if (video.duration_s && !duration) {
      setDuration(video.duration_s);
    }
  }, [video]);

  useEffect(() => {
    const isReady =
      currentVideo.status === 'ready_text' ||
      currentVideo.status === 'ready_full' ||
      currentVideo.status === 'completed' ||
      currentVideo.status === 'failed';
    if (isReady) return;

    const interval = setInterval(async () => {
      try {
        const updated = await api.getVideo(currentVideo.id);
        setCurrentVideo(updated);
        if (updated.duration_s && !duration) {
          setDuration(updated.duration_s);
        }
      } catch {
        // ignore polling errors
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [currentVideo.id, currentVideo.status, duration, setDuration]);

  const handleAsk = async (query: string, pause_t: number) => {
    setAsking(true);
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: query,
      pause_t,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const resp = await api.ask(currentVideo.id, { query, pause_t, session_id: sessionId });
      setSessionId(resp.session_id);
      const assistantMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: resp.answer,
        pause_t: resp.pause_t,
        citations: resp.citations,
        refusal: resp.refusal,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'Error communicating with assistant. Please try again.',
        pause_t,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '16px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <button
          onClick={onBack}
          style={{ padding: '6px 12px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}
        >
          ← Back to Library
        </button>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {currentVideo.title}
        </h2>
      </div>

      <IngestProgress status={currentVideo.status} metadata={currentVideo.metadata} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) 420px',
          gap: '24px',
          height: 'calc(100vh - 120px)',
        }}
        className="watch-layout"
      >
        {/* Left Side: Video Player, Timeline & Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
          <Player
            video={currentVideo}
            onTimeUpdate={setCurrentTime}
            onDurationChange={setDuration}
            registerPlayer={registerPlayer}
          />
          <UnlockBar currentTime={currentTime} duration={duration || currentVideo.duration_s || 0} />
          <QuickActions onActionClick={(prompt) => handleAsk(prompt, currentTime)} disabled={asking} />
        </div>

        {/* Right Side: Chat Assistant Panel */}
        <div style={{ height: '100%' }}>
          <ChatPanel
            messages={messages}
            currentTime={currentTime}
            onPause={pause}
            onAsk={handleAsk}
            onSeek={seekTo}
            isLoading={asking}
          />
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .watch-layout {
            grid-template-columns: 1fr !important;
            height: auto !important;
          }
        }
      `}</style>
    </div>
  );
};
