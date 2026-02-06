import { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  Toast,
} from 'gestalt';
import { AudioUploader } from './components/AudioUploader';
import { MoodBoard } from './components/MoodBoard';
import { MoodSliders } from './components/MoodSliders';
import { WaveformPlayer } from './components/WaveformPlayer';
import { useAudioAnalysis } from './hooks/useAudioAnalysis';
import { useMoodBoard } from './hooks/useMoodBoard';
import type { MoodSliders as MoodSlidersType, ImageResult } from './types';

function App() {
  const {
    sessionId,
    isAnalyzing,
    error: analysisError,
    moodSliders,
    images,
    analyze,
    reset,
  } = useAudioAnalysis();

  const { isRefining, error: refineError, refine } = useMoodBoard();

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [currentImages, setCurrentImages] = useState<ImageResult[]>([]);
  const [currentSliders, setCurrentSliders] = useState<MoodSlidersType | null>(null);

  const handleUpload = useCallback(
    async (file: File) => {
      setAudioFile(file);
      await analyze(file);
    },
    [analyze]
  );

  // Sync analysis results to local state
  useState(() => {
    if (images.length > 0) {
      setCurrentImages(images);
    }
    if (moodSliders) {
      setCurrentSliders(moodSliders);
    }
  });

  const handleSliderChange = useCallback(
    async (newSliders: MoodSlidersType) => {
      setCurrentSliders(newSliders);

      if (sessionId) {
        const result = await refine(sessionId, newSliders);
        if (result) {
          setCurrentImages(result.images);
        }
      }
    },
    [sessionId, refine]
  );

  const handleReset = useCallback(() => {
    reset();
    setAudioFile(null);
    setCurrentImages([]);
    setCurrentSliders(null);
  }, [reset]);

  const handleImageClick = useCallback((image: ImageResult) => {
    window.open(image.image_url, '_blank');
  }, []);

  const displayImages = currentImages.length > 0 ? currentImages : images;
  const displaySliders = currentSliders || moodSliders;
  const error = analysisError || refineError;

  return (
    <Box padding={4} maxWidth={1400} marginStart="auto" marginEnd="auto">
      <Box marginBottom={6}>
        <Flex justifyContent="between" alignItems="center">
          <Heading size="500">Evoke</Heading>
          {sessionId && (
            <Button text="Start Over" onClick={handleReset} size="sm" />
          )}
        </Flex>
        <Text color="subtle">Transform music into visual inspiration</Text>
      </Box>

      <Flex gap={6} wrap>
        <Box minWidth={300} maxWidth={400} flex="none">
          <Flex direction="column" gap={4}>
            <AudioUploader
              onUpload={handleUpload}
              isLoading={isAnalyzing}
              disabled={isAnalyzing}
            />

            {audioFile && <WaveformPlayer audioFile={audioFile} />}

            {displaySliders && (
              <MoodSliders
                sliders={displaySliders}
                onChange={handleSliderChange}
                disabled={isRefining}
              />
            )}

            {isRefining && (
              <Text size="200" color="subtle">
                Updating board...
              </Text>
            )}
          </Flex>
        </Box>

        <Box flex="grow" minWidth={0}>
          <MoodBoard images={displayImages} onImageClick={handleImageClick} />
        </Box>
      </Flex>

      {error && (
        <Box
          position="fixed"
          bottom
          left
          right
          padding={4}
          display="flex"
          justifyContent="center"
        >
          <Toast text={error} />
        </Box>
      )}
    </Box>
  );
}

export default App;
