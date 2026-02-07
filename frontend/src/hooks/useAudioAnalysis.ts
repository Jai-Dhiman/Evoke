import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { AnalyzeResponse, MoodSliders, ImageResult } from '../types';

interface UseAudioAnalysisReturn {
  embedding: number[] | null;
  isAnalyzing: boolean;
  isDemo: boolean;
  error: string | null;
  moodSliders: MoodSliders | null;
  images: ImageResult[];
  analyze: (file: File) => Promise<void>;
  loadDemo: () => Promise<void>;
  reset: () => void;
}

export function useAudioAnalysis(): UseAudioAnalysisReturn {
  const [embedding, setEmbedding] = useState<number[] | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moodSliders, setMoodSliders] = useState<MoodSliders | null>(null);
  const [images, setImages] = useState<ImageResult[]>([]);

  const analyze = useCallback(async (file: File) => {
    setIsAnalyzing(true);
    setError(null);
    setIsDemo(false);

    try {
      const result: AnalyzeResponse = await api.analyzeAudio(file);

      setEmbedding(result.embedding);
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

  const loadDemo = useCallback(async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const result: AnalyzeResponse = await api.demo();
      setEmbedding(result.embedding);
      setIsDemo(true);
      setMoodSliders({
        energy: result.mood_energy,
        valence: result.mood_valence,
        tempo: result.mood_tempo,
        texture: result.mood_texture,
      });
      setImages(result.images);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load demo';
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setEmbedding(null);
    setIsDemo(false);
    setMoodSliders(null);
    setImages([]);
    setError(null);
  }, []);

  return {
    embedding,
    isAnalyzing,
    isDemo,
    error,
    moodSliders,
    images,
    analyze,
    loadDemo,
    reset,
  };
}
