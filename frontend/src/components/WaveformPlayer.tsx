import { useRef, useState, useEffect, useCallback } from 'react';
import { Box, IconButton, Text } from 'gestalt';

interface WaveformPlayerProps {
  audioFile: File | null;
}

export function WaveformPlayer({ audioFile }: WaveformPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
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

  useEffect(() => {
    if (!audioFile || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reader = new FileReader();
    reader.onload = async () => {
      const audioContext = new AudioContext();
      const arrayBuffer = reader.result as ArrayBuffer;
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      const channelData = audioBuffer.getChannelData(0);
      const samples = 100;
      const blockSize = Math.floor(channelData.length / samples);

      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#767676';

      const barWidth = canvas.width / samples;
      const centerY = canvas.height / 2;

      for (let i = 0; i < samples; i++) {
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(channelData[i * blockSize + j]);
        }
        const amplitude = sum / blockSize;
        const barHeight = amplitude * canvas.height * 0.8;

        ctx.fillRect(
          i * barWidth + 1,
          centerY - barHeight / 2,
          barWidth - 2,
          barHeight
        );
      }

      audioContext.close();
    };

    reader.readAsArrayBuffer(audioFile);
  }, [audioFile]);

  const handlePlayPause = useCallback(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!audioFile) {
    return null;
  }

  return (
    <Box
      padding={4}
      rounding={3}
      color="elevationFloating"
      display="flex"
      alignItems="center"
      gap={4}
    >
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={handleEnded}
        />
      )}

      <IconButton
        accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
        icon={isPlaying ? 'pause' : 'play'}
        onClick={handlePlayPause}
        size="lg"
      />

      <Box flex="grow" position="relative" height={60}>
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            height: '100%',
          }}
        />
        {duration > 0 && (
          <Box
            position="absolute"
            top
            left
            height="100%"
            dangerouslySetInlineStyle={{
              __style: {
                width: `${(currentTime / duration) * 100}%`,
                backgroundColor: 'rgba(0, 132, 255, 0.3)',
                pointerEvents: 'none',
              },
            }}
          />
        )}
      </Box>

      <Text size="200">
        {formatTime(currentTime)} / {formatTime(duration)}
      </Text>
    </Box>
  );
}
