import { Masonry } from 'gestalt';
import { ImageCard } from './ImageCard';
import type { ImageResult } from '../types';

interface MoodBoardProps {
  images: ImageResult[];
  onImageClick?: (image: ImageResult) => void;
  isLoading?: boolean;
}

const SKELETON_HEIGHTS = [280, 220, 320, 240, 300, 260, 200, 340, 250, 290, 230, 310];

export function MoodBoard({ images, onImageClick, isLoading = false }: MoodBoardProps) {
  if (isLoading && images.length === 0) {
    return (
      <div style={{
        padding: 'var(--space-lg)',
        columnCount: 3,
        columnGap: '20px',
      }}>
        {SKELETON_HEIGHTS.map((height, i) => (
          <div
            key={i}
            className="evoke-skeleton"
            style={{
              height: `${height}px`,
              marginBottom: '20px',
              breakInside: 'avoid',
            }}
          />
        ))}
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="evoke-empty-state">
        <svg className="evoke-empty-state__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
        <h2 className="evoke-empty-state__title">Your gallery awaits</h2>
        <p className="evoke-empty-state__subtitle">
          Upload a piece of music and watch it transform into a curated collection of images
        </p>
      </div>
    );
  }

  return (
    <div className="evoke-board-enter" style={{ padding: 'var(--space-lg)' }}>
      <Masonry
        items={images}
        renderItem={({ data, itemIdx }) => (
          <ImageCard
            image={data}
            onClick={onImageClick}
            index={itemIdx}
          />
        )}
        minCols={2}
        gutterWidth={20}
        layout="flexible"
        columnWidth={240}
      />
    </div>
  );
}
