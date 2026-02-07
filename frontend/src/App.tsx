import { useState, useCallback, useEffect } from 'react';
import { AudioUploader } from './components/AudioUploader';
import { MoodBoard } from './components/MoodBoard';
import { MoodSliders } from './components/MoodSliders';
import { WaveformPlayer } from './components/WaveformPlayer';
import { useAudioAnalysis } from './hooks/useAudioAnalysis';
import { useMoodBoard } from './hooks/useMoodBoard';
import type { MoodSliders as MoodSlidersType, ImageResult } from './types';

function App() {
  const {
    embedding,
    isAnalyzing,
    isDemo,
    error: analysisError,
    moodSliders,
    images,
    analyze,
    loadDemo,
    reset,
  } = useAudioAnalysis();

  const { isRefining, error: refineError, refine } = useMoodBoard();

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [currentImages, setCurrentImages] = useState<ImageResult[]>([]);
  const [currentSliders, setCurrentSliders] = useState<MoodSlidersType | null>(null);
  const [showSlowMessage, setShowSlowMessage] = useState(false);

  const handleUpload = useCallback(
    async (file: File) => {
      setAudioFile(file);
      await analyze(file);
    },
    [analyze]
  );

  const handleDemo = useCallback(async () => {
    await loadDemo();
    // Fetch demo.mp3 so WaveformPlayer works
    try {
      const response = await fetch('/demo.mp3');
      if (response.ok) {
        const blob = await response.blob();
        const file = new File([blob], 'demo.mp3', { type: 'audio/mpeg' });
        setAudioFile(file);
      }
    } catch {
      // Demo audio is optional for waveform display
    }
  }, [loadDemo]);

  useEffect(() => {
    if (images.length > 0) {
      setCurrentImages(images);
    }
    if (moodSliders) {
      setCurrentSliders(moodSliders);
    }
  }, [images, moodSliders]);

  // Show slow message after 5 seconds of analyzing
  useEffect(() => {
    if (!isAnalyzing) {
      setShowSlowMessage(false);
      return;
    }
    const timer = setTimeout(() => setShowSlowMessage(true), 5000);
    return () => clearTimeout(timer);
  }, [isAnalyzing]);

  const handleSliderChange = useCallback(
    async (newSliders: MoodSlidersType) => {
      setCurrentSliders(newSliders);

      if (embedding) {
        const result = await refine(embedding, newSliders);
        if (result) {
          setCurrentImages(result.images);
        }
      }
    },
    [embedding, refine]
  );

  const handleReset = useCallback(() => {
    reset();
    setAudioFile(null);
    setCurrentImages([]);
    setCurrentSliders(null);
    setShowSlowMessage(false);
  }, [reset]);

  const handleImageClick = useCallback((image: ImageResult) => {
    window.open(image.image_url, '_blank');
  }, []);

  const displayImages = currentImages.length > 0 ? currentImages : images;
  const displaySliders = currentSliders || moodSliders;
  const error = analysisError || refineError;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      background: 'var(--color-bg)',
    }}>
      {/* Top bar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-md) var(--space-lg)',
        borderBottom: '1px solid var(--color-border-subtle)',
        flexShrink: 0,
      }}>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: '24px',
          fontWeight: 400,
          color: 'var(--color-text)',
          margin: 0,
        }}>
          Evoke
        </h1>
        {embedding && (
          <button
            onClick={handleReset}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              color: 'var(--color-text-secondary)',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 16px',
              cursor: 'pointer',
              transition: 'color var(--timing-fast) var(--ease-out), border-color var(--timing-fast) var(--ease-out)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-text)';
              e.currentTarget.style.borderColor = 'var(--color-text-muted)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-text-secondary)';
              e.currentTarget.style.borderColor = 'var(--color-border)';
            }}
          >
            Start Over
          </button>
        )}
      </header>

      {/* Main content */}
      <div style={{
        display: 'flex',
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
      }}>
        {/* Sidebar */}
        <aside style={{
          width: '360px',
          flexShrink: 0,
          borderRight: '1px solid var(--color-border-subtle)',
          overflowY: 'auto',
          padding: 'var(--space-lg)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-lg)',
        }}>
          <p style={{
            fontFamily: 'var(--font-display)',
            fontStyle: 'italic',
            fontSize: '15px',
            color: 'var(--color-text-secondary)',
            margin: 0,
            lineHeight: 1.6,
          }}>
            Transform music into visual inspiration
          </p>

          {!embedding && !isAnalyzing && (
            <>
              <AudioUploader
                onUpload={handleUpload}
                isLoading={isAnalyzing}
                disabled={isAnalyzing}
              />

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-sm)',
              }}>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border-subtle)' }} />
                <span style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '12px',
                  color: 'var(--color-text-muted)',
                  padding: '0 var(--space-xs)',
                }}>or</span>
                <div style={{ flex: 1, height: '1px', background: 'var(--color-border-subtle)' }} />
              </div>

              <button
                onClick={handleDemo}
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  color: 'var(--color-text)',
                  background: 'var(--color-surface-raised)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 24px',
                  cursor: 'pointer',
                  transition: 'border-color var(--timing-fast) var(--ease-out), background var(--timing-fast) var(--ease-out)',
                  width: '100%',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-text-muted)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                }}
              >
                Try Demo
              </button>
            </>
          )}

          {embedding && !isAnalyzing && (
            <AudioUploader
              onUpload={handleUpload}
              isLoading={isAnalyzing}
              disabled={isAnalyzing}
            />
          )}

          {isAnalyzing && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 'var(--space-sm)',
              padding: 'var(--space-lg) 0',
            }}>
              <p style={{
                fontSize: '14px',
                color: 'var(--color-text-secondary)',
                margin: 0,
              }}>
                Analyzing...
              </p>
              {showSlowMessage && (
                <p style={{
                  fontSize: '13px',
                  color: 'var(--color-text-muted)',
                  margin: 0,
                  textAlign: 'center',
                }}>
                  Warming up the model, this may take a moment...
                </p>
              )}
            </div>
          )}

          {audioFile && !isAnalyzing && <WaveformPlayer audioFile={audioFile} />}

          {isDemo && !isAnalyzing && (
            <p style={{
              fontSize: '13px',
              color: 'var(--color-text-muted)',
              margin: 0,
              lineHeight: 1.5,
            }}>
              Listening to a demo track. Upload your own for a custom board.
            </p>
          )}

          {displaySliders && (
            <MoodSliders
              sliders={displaySliders}
              onChange={handleSliderChange}
              disabled={isRefining}
            />
          )}

          {isRefining && (
            <p style={{
              fontSize: '13px',
              color: 'var(--color-text-muted)',
              margin: 0,
            }}>
              Updating board...
            </p>
          )}
        </aside>

        {/* Main board area */}
        <main style={{
          flex: 1,
          minWidth: 0,
          overflowY: 'auto',
        }}>
          <MoodBoard
            images={displayImages}
            onImageClick={handleImageClick}
            isLoading={isAnalyzing}
          />
        </main>
      </div>

      {/* Error toast */}
      {error && (
        <div style={{
          position: 'fixed',
          bottom: 'var(--space-lg)',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--color-surface-raised)',
          border: '1px solid var(--color-error)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-sm) var(--space-lg)',
          color: 'var(--color-error)',
          fontSize: '14px',
          fontFamily: 'var(--font-body)',
          boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
          zIndex: 1000,
          animation: 'fade-up var(--timing-normal) var(--ease-out)',
        }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default App;
