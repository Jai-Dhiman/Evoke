import { Hono } from 'hono';
import type { Env } from '../lib/types';
import { analyzeAudio } from '../lib/ml-client';
import { search } from '../lib/vectorstore';

const app = new Hono<{ Bindings: Env }>();

app.post('/api/analyze', async (c) => {
  const body = await c.req.parseBody();
  const audioFile = body['audio'];

  if (!(audioFile instanceof File)) {
    return c.json({ error: 'audio file is required' }, 400);
  }

  const audioData = await audioFile.arrayBuffer();
  const result = await analyzeAudio(c.env.ML_SERVICE_URL, audioData, audioFile.name);

  const images = search(result.embedding, 20);

  return c.json({
    embedding: result.embedding,
    mood_energy: result.mood_energy,
    mood_valence: result.mood_valence,
    mood_tempo: result.mood_tempo,
    mood_texture: result.mood_texture,
    images,
  });
});

export default app;
