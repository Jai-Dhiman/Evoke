import { useState, useEffect, useCallback } from 'react';
import type { ImageResult } from '../types';

interface ImageCardProps {
  image: ImageResult;
  onClick?: (image: ImageResult) => void;
  index?: number;
}

export function ImageCard({ image, onClick, index = 0 }: ImageCardProps) {
  const [loaded, setLoaded] = useState(false);
  const [aspectRatio, setAspectRatio] = useState(4 / 5);

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      if (img.naturalWidth > 0 && img.naturalHeight > 0) {
        setAspectRatio(img.naturalWidth / img.naturalHeight);
      }
      setLoaded(true);
    };
    img.onerror = () => {
      setLoaded(true);
    };
    img.src = image.image_url;
  }, [image.image_url]);

  const handleClick = useCallback(() => {
    onClick?.(image);
  }, [image, onClick]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.(image);
    }
  }, [image, onClick]);

  const staggerClass = index <= 12 ? `evoke-stagger-${index}` : '';

  return (
    <div
      className={`evoke-image-card ${staggerClass}`}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {!loaded && (
        <div
          className="evoke-skeleton"
          style={{
            width: '100%',
            paddingBottom: `${(1 / aspectRatio) * 100}%`,
          }}
        />
      )}
      <img
        className="evoke-image-card__img"
        src={image.image_url}
        alt={`Generated image ${image.id}`}
        loading="lazy"
        style={{
          display: loaded ? 'block' : 'none',
          aspectRatio: `${aspectRatio}`,
        }}
        onLoad={() => setLoaded(true)}
      />
      <div className="evoke-image-card__overlay">
        <span className="evoke-image-card__overlay-text">View full size</span>
      </div>
    </div>
  );
}
