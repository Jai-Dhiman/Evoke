import { useCallback, useRef, useState } from 'react';

interface AudioUploaderProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const VALID_EXTENSIONS = /\.(mp3|wav|ogg|flac)$/i;
const VALID_TYPES = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/flac'];

export function AudioUploader({
  onUpload,
  isLoading,
  disabled = false,
}: AudioUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      if (!VALID_TYPES.includes(file.type) && !VALID_EXTENSIONS.test(file.name)) {
        setError('Please upload an audio file (MP3, WAV, OGG, or FLAC)');
        return;
      }
      setFileName(file.name);
      onUpload(file);
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const className = [
    'evoke-uploader',
    dragOver && 'evoke-uploader--drag-over',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={className}
      onClick={isLoading ? undefined : handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        onChange={handleChange}
        style={{ display: 'none' }}
      />

      {isLoading ? (
        <>
          <div className="evoke-dot-pulse">
            <div className="evoke-dot-pulse__dot" />
            <div className="evoke-dot-pulse__dot" />
            <div className="evoke-dot-pulse__dot" />
          </div>
          <p style={{
            fontSize: '14px',
            color: 'var(--color-text-secondary)',
            margin: 0,
          }}>
            Analyzing your music...
          </p>
        </>
      ) : (
        <>
          <svg className="evoke-uploader__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12l7-7 7 7" />
          </svg>
          <p className="evoke-uploader__title">Drop your audio here</p>
          <p className="evoke-uploader__subtitle">or</p>
          <button
            className="evoke-uploader__choose-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleClick();
            }}
            disabled={disabled}
          >
            Choose File
          </button>
          {fileName && (
            <p className="evoke-uploader__file-name">
              Selected: {fileName}
            </p>
          )}
          {error && (
            <p className="evoke-uploader__error">{error}</p>
          )}
          <p className="evoke-uploader__subtitle">
            Supports MP3, WAV, OGG, FLAC (max 30 seconds)
          </p>
        </>
      )}
    </div>
  );
}
