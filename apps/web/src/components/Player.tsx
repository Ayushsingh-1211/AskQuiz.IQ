import React from 'react';
import { Html5Player } from './Html5Player';
import { YouTubePlayer } from './YouTubePlayer';
import { Video } from '../api/types';

interface PlayerProps {
  video: Video;
  onTimeUpdate: (t: number) => void;
  onDurationChange: (d: number) => void;
  onPlayStateChange?: (playing: boolean) => void;
  registerPlayer: (seekFn: (t: number) => void, pauseFn: () => void) => void;
}

export const Player: React.FC<PlayerProps> = ({
  video,
  onTimeUpdate,
  onDurationChange,
  onPlayStateChange,
  registerPlayer,
}) => {
  const isYouTube = !!video.url && (video.url.includes('youtube.com') || video.url.includes('youtu.be'));

  if (isYouTube && !video.stream_url) {
    return (
      <YouTubePlayer
        url={video.url!}
        onTimeUpdate={onTimeUpdate}
        onDurationChange={onDurationChange}
        registerPlayer={registerPlayer}
      />
    );
  }

  // Resolve stream URL using configured VITE_API_URL
  const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
  let rawStream = video.stream_url || `/api/v1/videos/${video.id}/stream`;
  let streamUrl = rawStream;

  if (!rawStream.startsWith('http')) {
    streamUrl = `${apiBase}${rawStream}`;
  } else if (rawStream.includes('localhost') && apiBase.includes('trycloudflare.com')) {
    try {
      const u = new URL(rawStream);
      streamUrl = `${apiBase}${u.pathname}${u.search}`;
    } catch {
      streamUrl = rawStream;
    }
  }

  const captionsUrl = `${apiBase}/api/v1/videos/${video.id}/captions`;

  return (
    <Html5Player
      streamUrl={streamUrl}
      captionsUrl={captionsUrl}
      onTimeUpdate={onTimeUpdate}
      onDurationChange={onDurationChange}
      onPlayStateChange={onPlayStateChange}
      registerPlayer={registerPlayer}
    />
  );
};
