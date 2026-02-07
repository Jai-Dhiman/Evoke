import { Hono } from 'hono';
import type { Env, RefineRequest } from '../lib/types';
import { refineEmbedding, search } from '../lib/vectorstore';

const app = new Hono<{ Bindings: Env }>();

app.post('/api/refine', async (c) => {
  const body = await c.req.json<RefineRequest>();

  if (!body.embedding || !Array.isArray(body.embedding)) {
    return c.json({ error: 'embedding is required' }, 400);
  }

  const refined = refineEmbedding(
    body.embedding,
    body.energy,
    body.valence,
    body.tempo,
    body.texture,
  );

  const images = search(refined, 20);

  return c.json({
    mood_energy: body.energy,
    mood_valence: body.valence,
    mood_tempo: body.tempo,
    mood_texture: body.texture,
    images,
  });
});

export default app;
