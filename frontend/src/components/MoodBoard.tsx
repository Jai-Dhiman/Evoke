import { Box, Masonry, Text } from 'gestalt';
import { ImageCard } from './ImageCard';
import type { ImageResult } from '../types';

interface MoodBoardProps {
  images: ImageResult[];
  onImageClick?: (image: ImageResult) => void;
}

export function MoodBoard({ images, onImageClick }: MoodBoardProps) {
  if (images.length === 0) {
    return (
      <Box
        padding={8}
        display="flex"
        alignItems="center"
        justifyContent="center"
        minHeight={400}
      >
        <Text color="subtle" size="300">
          Upload audio to generate your mood board
        </Text>
      </Box>
    );
  }

  return (
    <Box padding={4}>
      <Masonry
        items={images}
        renderItem={({ data }) => (
          <ImageCard image={data} onClick={onImageClick} />
        )}
        minCols={2}
        gutterWidth={16}
        layout="flexible"
        columnWidth={200}
      />
    </Box>
  );
}
