import { Box, Image, TapArea } from 'gestalt';
import type { ImageResult } from '../types';

interface ImageCardProps {
  image: ImageResult;
  onClick?: (image: ImageResult) => void;
}

export function ImageCard({ image, onClick }: ImageCardProps) {
  const handleTap = () => {
    onClick?.(image);
  };

  return (
    <TapArea onTap={handleTap} rounding={3}>
      <Box
        rounding={3}
        overflow="hidden"
        borderStyle="sm"
        color="elevationFloating"
      >
        <Image
          src={image.image_url}
          alt={`Image ${image.id}`}
          naturalWidth={1}
          naturalHeight={1}
          fit="cover"
        />
      </Box>
    </TapArea>
  );
}
