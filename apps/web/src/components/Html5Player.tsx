import React, { useRef, useEffect } from 'react';

interface Html5PlayerProps {
  streamUrl: string;
  captionsUrl?: string;
  onTimeUpdate: (t: number) => void;
  onDurationChange: (d: number) => void;
  onPlayStateChange?: (playing: boolean) => void;
  registerPlayer: (seekFn: (t: number) => void, pauseFn: () => void) => void;
}

export const Html5Player: React.FC<Html5PlayerProps> = ({
  streamUrl,
  captionsUrl,
  onTimeUpdate,
  onDurationChange,
  onPlayStateChange,
  registerPlayer,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    registerPlayer(
      (t: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = t;
        }
      },
      () => {
        if (videoRef.current) {
          videoRef.current.pause();
        }
      }
    );
  }, [registerPlayer]);

  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
      <video
        ref={videoRef}
        src={streamUrl}
        controls
        playsInline
        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        onTimeUpdate={() => {
          if (videoRef.current) {
            onTimeUpdate(videoRef.current.currentTime);
          }
        }}
        onLoadedMetadata={() => {
          if (videoRef.current) {
            onDurationChange(videoRef.current.duration);
          }
        }}
        onPlay={() => onPlayStateChange && onPlayStateChange(true)}
        onPause={() => onPlayStateChange && onPlayStateChange(false)}
      >
        {captionsUrl && (
          <track
            default
            kind="subtitles"
            label="English"
            srcLang="en"
            src={captionsUrl}
          />
        )}
      </video>
    </div>
  );
};
