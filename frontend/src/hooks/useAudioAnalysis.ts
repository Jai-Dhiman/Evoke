import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { AnalyzeResponse, MoodSliders, ImageResult } from '../types';

interface UseAudioAnalysisReturn {
  sessionId: string | null;
  isAnalyzing: boolean;
  error: string | null;
  moodSliders: MoodSliders | null;
  images: ImageResult[];
  analyze: (file: File) => Promise<void>;
  reset: () => void;
}

export function useAudioAnalysis(): UseAudioAnalysisReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moodSliders, setMoodSliders] = useState<MoodSliders | null>(null);
  const [images, setImages] = useState<ImageResult[]>([]);

  const analyze = useCallback(async (file: File) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      // Create a new session
      const session = await api.createSession();
      setSessionId(session.session_id);

      // Analyze the audio
      const result: AnalyzeResponse = await api.analyzeAudio(
        session.session_id,
        file
      );

      setMoodSliders({
        energy: result.mood_energy,
        valence: result.mood_valence,
        tempo: result.mood_tempo,
        texture: result.mood_texture,
      });
      setImages(result.images);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setSessionId(null);
    setMoodSliders(null);
    setImages([]);
    setError(null);
  }, []);

  return {
    sessionId,
    isAnalyzing,
    error,
    moodSliders,
    images,
    analyze,
    reset,
  };
}
