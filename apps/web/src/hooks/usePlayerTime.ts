import { useState, useCallback, useRef } from 'react';

export function usePlayerTime() {
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const seekHandlerRef = useRef<((t: number) => void) | null>(null);
  const pauseHandlerRef = useRef<(() => void) | null>(null);

  const registerPlayer = useCallback((seekFn: (t: number) => void, pauseFn: () => void) => {
    seekHandlerRef.current = seekFn;
    pauseHandlerRef.current = pauseFn;
  }, []);

  const pause = useCallback(() => {
    if (pauseHandlerRef.current) {
      pauseHandlerRef.current();
    }
  }, []);

  const seekTo = useCallback((t: number) => {
    if (seekHandlerRef.current) {
      seekHandlerRef.current(t);
    }
  }, []);

  return {
    currentTime,
    setCurrentTime,
    duration,
    setDuration,
    isPlaying,
    setIsPlaying,
    pause,
    seekTo,
    registerPlayer,
  };
}
