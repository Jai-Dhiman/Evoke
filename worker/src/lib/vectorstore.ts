import type { ImageEntry, DirectionVectors, DemoData, ImageResult } from './types';
import imagesData from '../data/images.json';
import directionsData from '../data/directions.json';
import demoData from '../data/demo.json';

const images: ImageEntry[] = imagesData as ImageEntry[];
const directions: DirectionVectors = directionsData as DirectionVectors;
const demo: DemoData = demoData as DemoData;

function l2Distance(a: number[], b: number[]): number {
  let sum = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    const d = a[i] - b[i];
    sum += d * d;
  }
  return Math.sqrt(sum);
}

export function search(embedding: number[], topK: number): ImageResult[] {
  const scored: { index: number; dist: number }[] = [];
  for (let i = 0; i < images.length; i++) {
    const dist = l2Distance(embedding, images[i].embedding);
    scored.push({ index: i, dist });
  }

  scored.sort((a, b) => a.dist - b.dist);

  const k = Math.min(topK, scored.length);
  const results: ImageResult[] = [];
  for (let i = 0; i < k; i++) {
    const idx = scored[i].index;
    results.push({
      id: idx,
      image_url: images[idx].url,
      score: scored[i].dist,
    });
  }

  return results;
}

export function refineEmbedding(
  base: number[],
  energy: number,
  valence: number,
  tempo: number,
  texture: number,
): number[] {
  const dim = base.length;
  const refined = base.slice();

  for (let i = 0; i < dim; i++) {
    let adjustment = 0;
    if (i < directions.energy.length) {
      adjustment += directions.energy[i] * (energy - 0.5) * 0.2;
    }
    if (i < directions.valence.length) {
      adjustment += directions.valence[i] * (valence - 0.5) * 0.2;
    }
    if (i < directions.tempo.length) {
      adjustment += directions.tempo[i] * (tempo - 0.5) * 0.15;
    }
    if (i < directions.texture.length) {
      adjustment += directions.texture[i] * (texture - 0.5) * 0.15;
    }
    refined[i] += adjustment;
  }

  // L2 normalize
  let norm = 0;
  for (const v of refined) {
    norm += v * v;
  }
  norm = Math.sqrt(norm);
  if (norm > 0) {
    for (let i = 0; i < refined.length; i++) {
      refined[i] /= norm;
    }
  }

  return refined;
}

export function getDemo(): DemoData {
  return demo;
}

export function imageCount(): number {
  return images.length;
}
