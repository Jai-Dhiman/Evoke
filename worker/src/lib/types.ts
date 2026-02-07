export interface Env {
  ML_SERVICE_URL: string;
}

export interface ImageEntry {
  url: string;
  embedding: number[];
}

export interface DirectionVectors {
  energy: number[];
  valence: number[];
  tempo: number[];
  texture: number[];
}

export interface DemoData {
  embedding: number[];
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
  images: ImageResult[];
}

export interface ImageResult {
  id: number;
  image_url: string;
  score: number;
}

export interface AnalyzeResponse {
  embedding: number[];
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
  images: ImageResult[];
}

export interface RefineRequest {
  embedding: number[];
  energy: number;
  valence: number;
  tempo: number;
  texture: number;
}

export interface RefineResponse {
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
  images: ImageResult[];
}
