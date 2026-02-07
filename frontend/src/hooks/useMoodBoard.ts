import { useState, useCallback, useRef } from 'react';
import { api } from '../api/client';
import type { MoodSliders, ImageResult } from '../types';

interface UseMoodBoardReturn {
  isRefining: boolean;
  error: string | null;
  refine: (
    embedding: number[],
    sliders: MoodSliders
  ) => Promise<{ images: ImageResult[]; sliders: MoodSliders } | null>;
}

export function useMoodBoard(): UseMoodBoardReturn {
  const [isRefining, setIsRefining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const refine = useCallback(
    async (
      embedding: number[],
      sliders: MoodSliders
    ): Promise<{ images: ImageResult[]; sliders: MoodSliders } | null> => {
      // Clear any pending debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      return new Promise((resolve) => {
        debounceRef.current = setTimeout(async () => {
          setIsRefining(true);
          setError(null);

          try {
            const result = await api.refine({
              embedding,
              energy: sliders.energy,
              valence: sliders.valence,
              tempo: sliders.tempo,
              texture: sliders.texture,
            });

            resolve({
              images: result.images,
              sliders: {
                energy: result.mood_energy,
                valence: result.mood_valence,
                tempo: result.mood_tempo,
                texture: result.mood_texture,
              },
            });
          } catch (err) {
            const message = err instanceof Error ? err.message : 'Refinement failed';
            setError(message);
            resolve(null);
          } finally {
            setIsRefining(false);
          }
        }, 300); // 300ms debounce
      });
    },
    []
  );

  return {
    isRefining,
    error,
    refine,
  };
}
