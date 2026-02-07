interface MLAnalyzeResult {
  embedding: number[];
  mood_energy: number;
  mood_valence: number;
  mood_tempo: number;
  mood_texture: number;
}

export async function analyzeAudio(
  mlServiceUrl: string,
  audioData: ArrayBuffer,
  filename: string,
): Promise<MLAnalyzeResult> {
  const formData = new FormData();
  const blob = new Blob([audioData]);
  formData.append('audio', blob, filename);

  const response = await fetch(`${mlServiceUrl}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`ML service error (${response.status}): ${text}`);
  }

  return response.json();
}
