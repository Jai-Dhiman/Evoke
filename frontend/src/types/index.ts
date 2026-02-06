export interface ImageResult {
  id: number;
  image_url: string;
  score: number;
  width?: number;
  height?: number;
}

export interface MoodSliders {
  energy: number;
  valence: number;
  tempo: number;
  texture: number;
}

export interface SessionResponse {
  session_id: string;
}

export interface AnalyzeResponse {
  session_id: string;
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
  images: ImageResult[];
}

export interface BoardResponse {
  session_id: string;
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
  images: ImageResult[];
}

export interface RefineRequest {
  session_id: string;
  energy: number;
  valence: number;
  tempo: number;
  texture: number;
}
