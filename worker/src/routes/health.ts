import { Hono } from 'hono';
import type { Env } from '../lib/types';
import { imageCount } from '../lib/vectorstore';

const app = new Hono<{ Bindings: Env }>();

app.get('/health', async (c) => {
  const services: Record<string, string> = {};

  // Vectorstore check
  const count = imageCount();
  services.vectorstore = count > 0 ? 'ok' : 'error';

  // ML service check
  try {
    const resp = await fetch(`${c.env.ML_SERVICE_URL}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    services.ml = resp.ok ? 'ok' : 'error';
  } catch {
    services.ml = 'unreachable';
  }

  const status = services.vectorstore === 'ok' ? 'ok' : 'degraded';
  return c.json({ status, services });
});

export default app;
