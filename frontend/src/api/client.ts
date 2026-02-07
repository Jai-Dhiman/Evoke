import type {
  AnalyzeResponse,
  RefineRequest,
  RefineResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new ApiError(response.status, error.error || 'Request failed');
  }

  return response.json();
}

export const api = {
  analyzeAudio: (audioFile: File): Promise<AnalyzeResponse> => {
    const formData = new FormData();
    formData.append('audio', audioFile);

    return request('/api/analyze', {
      method: 'POST',
      body: formData,
    });
  },

  refine: (data: RefineRequest): Promise<RefineResponse> =>
    request('/api/refine', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }),

  demo: (): Promise<AnalyzeResponse> =>
    request('/api/demo', { method: 'POST' }),

  healthCheck: (): Promise<{ status: string; services: Record<string, string> }> =>
    request('/health'),
};

export { ApiError };
