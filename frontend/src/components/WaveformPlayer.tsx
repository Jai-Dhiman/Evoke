import { useRef, useState, useEffect, useCallback } from 'react';

interface WaveformPlayerProps {
  audioFile: File | null;
}

const BAR_COUNT = 80;
const ACCENT = '#c8956c';
const PLAYED_COLOR = '#ffffff';
const REFLECTION_ALPHA = 0.2;

export function WaveformPlayer({ audioFile }: WaveformPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const amplitudesRef = useRef<number[]>([]);
  const rafRef = useRef<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (audioFile) {
      const url = URL.createObjectURL(audioFile);
      setAudioUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    setAudioUrl(null);
  }, [audioFile]);

  // Decode audio and compute amplitude data
  useEffect(() => {
    if (!audioFile) return;

    const reader = new FileReader();
    reader.onload = async () => {
      const audioContext = new AudioContext();
      const arrayBuffer = reader.result as ArrayBuffer;
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const channelData = audioBuffer.getChannelData(0);
      const blockSize = Math.floor(channelData.length / BAR_COUNT);

      const amps: number[] = [];
      for (let i = 0; i < BAR_COUNT; i++) {
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(channelData[i * blockSize + j]);
        }
        amps.push(sum / blockSize);
      }

      // Normalize to 0-1
      const maxAmp = Math.max(...amps, 0.01);
      amplitudesRef.current = amps.map((a) => a / maxAmp);

      audioContext.close();
      drawWaveform(0);
    };

    reader.readAsArrayBuffer(audioFile);
  }, [audioFile]);

  const drawWaveform = useCallback((progress: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const amps = amplitudesRef.current;
    if (amps.length === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    const barWidth = w / BAR_COUNT;
    const gap = 2;
    const centerY = h * 0.45;
    const maxBarHeight = h * 0.38;
    const playedIndex = progress * BAR_COUNT;

    for (let i = 0; i < BAR_COUNT; i++) {
      const amp = amps[i];
      const barH = Math.max(amp * maxBarHeight, 2);
      const x = i * barWidth + gap / 2;
      const bw = barWidth - gap;
      const isPlayed = i < playedIndex;

      // Main bar
      ctx.save();
      if (isPlayed) {
        ctx.fillStyle = PLAYED_COLOR;
        ctx.shadowColor = ACCENT;
        ctx.shadowBlur = 6;
      } else {
        ctx.fillStyle = ACCENT;
        ctx.globalAlpha = 0.4 + amp * 0.6;
      }

      roundedRect(ctx, x, centerY - barH, bw, barH, 1.5);
      ctx.fill();
      ctx.restore();

      // Reflection below centerline
      ctx.save();
      ctx.globalAlpha = REFLECTION_ALPHA * (isPlayed ? 0.6 : 0.3 + amp * 0.3);
      ctx.fillStyle = isPlayed ? PLAYED_COLOR : ACCENT;
      const reflH = barH * 0.5;
      roundedRect(ctx, x, centerY + 1, bw, reflH, 1.5);
      ctx.fill();
      ctx.restore();
    }
  }, []);

  function roundedRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  // Animation loop for playback
  useEffect(() => {
    if (!isPlaying) return;

    const tick = () => {
      const audio = audioRef.current;
      if (audio && audio.duration > 0) {
        const progress = audio.currentTime / audio.duration;
        setCurrentTime(audio.currentTime);
        drawWaveform(progress);
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying, drawWaveform]);

  // ResizeObserver to redraw on container resize
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;

    const observer = new ResizeObserver(() => {
      const audio = audioRef.current;
      const progress = audio && audio.duration > 0
        ? audio.currentTime / audio.duration
        : 0;
      drawWaveform(progress);
    });

    observer.observe(wrap);
    return () => observer.disconnect();
  }, [drawWaveform]);

  const handlePlayPause = useCallback(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const audio = audioRef.current;
    const canvas = canvasRef.current;
    if (!audio || !canvas || !audio.duration) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const progress = x / rect.width;
    audio.currentTime = progress * audio.duration;
    setCurrentTime(audio.currentTime);
    drawWaveform(progress);
  }, [drawWaveform]);

  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    drawWaveform(1);
  }, [drawWaveform]);

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!audioFile) {
    return null;
  }

  return (
    <div className="evoke-waveform">
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={handleEnded}
        />
      )}

      <button
        className="evoke-waveform__play-btn"
        onClick={handlePlayPause}
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <svg viewBox="0 0 16 16">
            <rect x="3" y="2" width="4" height="12" rx="1" />
            <rect x="9" y="2" width="4" height="12" rx="1" />
          </svg>
        ) : (
          <svg viewBox="0 0 16 16">
            <path d="M4 2.5v11l9-5.5z" />
          </svg>
        )}
      </button>

      <div className="evoke-waveform__canvas-wrap" ref={wrapRef}>
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
        />
      </div>

      <span className="evoke-waveform__time">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
    </div>
  );
}
