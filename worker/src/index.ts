import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { Env } from './lib/types';
import analyzeRoutes from './routes/analyze';
import refineRoutes from './routes/refine';
import demoRoutes from './routes/demo';
import healthRoutes from './routes/health';

const app = new Hono<{ Bindings: Env }>();

app.use('/api/*', cors());

app.route('/', analyzeRoutes);
app.route('/', refineRoutes);
app.route('/', demoRoutes);
app.route('/', healthRoutes);

export default app;
