import { useCallback, useRef, useState } from 'react';
import { Box, Button, Text, Spinner } from 'gestalt';

interface AudioUploaderProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function AudioUploader({
  onUpload,
  isLoading,
  disabled = false,
}: AudioUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/flac'];
      if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|ogg|flac)$/i)) {
        alert('Please upload an audio file (MP3, WAV, OGG, or FLAC)');
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

  return (
    <Box
      padding={6}
      rounding={4}
      borderStyle="lg"
      color={dragOver ? 'secondary' : 'default'}
      display="flex"
      direction="column"
      alignItems="center"
      justifyContent="center"
      minHeight={200}
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
        <Box display="flex" direction="column" alignItems="center" gap={4}>
          <Spinner show accessibilityLabel="Analyzing audio" />
          <Text>Analyzing your music...</Text>
        </Box>
      ) : (
        <Box display="flex" direction="column" alignItems="center" gap={4}>
          <Text size="400" weight="bold">
            Drop your audio file here
          </Text>
          <Text color="subtle">or</Text>
          <Button
            text="Choose File"
            onClick={handleClick}
            disabled={disabled}
            size="lg"
          />
          {fileName && (
            <Text size="200" color="subtle">
              Selected: {fileName}
            </Text>
          )}
          <Text size="100" color="subtle">
            Supports MP3, WAV, OGG, FLAC (max 30 seconds)
          </Text>
        </Box>
      )}
    </Box>
  );
}
