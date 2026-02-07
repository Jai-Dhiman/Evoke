import { Hono } from 'hono';
import type { Env } from '../lib/types';
import { getDemo } from '../lib/vectorstore';

const app = new Hono<{ Bindings: Env }>();

app.post('/api/demo', (c) => {
  const demo = getDemo();
  return c.json({
    embedding: demo.embedding,
    mood_energy: demo.mood_energy,
    mood_valence: demo.mood_valence,
    mood_tempo: demo.mood_tempo,
    mood_texture: demo.mood_texture,
    images: demo.images,
  });
});

export default app;
