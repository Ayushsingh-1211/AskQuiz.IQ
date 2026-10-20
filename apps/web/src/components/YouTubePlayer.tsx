import React, { useRef, useEffect } from 'react';

interface YouTubePlayerProps {
  url: string;
  onTimeUpdate: (t: number) => void;
  onDurationChange: (d: number) => void;
  registerPlayer: (seekFn: (t: number) => void, pauseFn: () => void) => void;
}

export const YouTubePlayer: React.FC<YouTubePlayerProps> = ({
  url,
  onTimeUpdate,
  onDurationChange,
  registerPlayer,
}) => {
  // Extract YouTube video ID
  const getYouTubeId = (u: string): string => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = u.match(regExp);
    return match && match[2].length === 11 ? match[2] : '';
  };

  const videoId = getYouTubeId(url);

  useEffect(() => {
    registerPlayer(
      (_t: number) => {},
      () => {}
    );
  }, [registerPlayer]);

  if (!videoId) {
    return (
      <div style={{ width: '100%', aspectRatio: '16/9', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000', color: '#fff' }}>
        Invalid YouTube URL
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
      <iframe
        src={`https://www.youtube.com/embed/${videoId}?enablejsapi=1`}
        title="YouTube video player"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        style={{ width: '100%', height: '100%', border: 'none' }}
      />
    </div>
  );
};
